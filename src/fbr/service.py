# src\fbr\service.py

import asyncio
from typing import List, Literal, cast
from uuid import UUID

from src.auth.user import AuthUser
from src.config import get_setting
from src.exceptions import (
    BadRequestException,
    InternalServerErrorException,
)
from src.fbr.schemas import (
    FBRIntegrationRequest,
    FBRIntegrationResponse,
    FBRIntegrationScenarioResultResponse,
    FBRParsedResponse,
    FBRSubmissionRequest,
    FBRSubmissionResponse,
    FBRUOMRequest,
    FBRUOMResponse,
    FBRValidationRequest,
    FBRValidationResponse,
    ScenarioPayload,
)
from src.fbr.utils import (
    build_fbr_invoice,
    generate_scenario_payloads,
    get_fbr_uom,
    parse_fbr_response,
    send_fbr_request,
)
from src.invoices.enums import InvoiceFBRStatusEnum, InvoiceStatusEnum
from src.invoices.schemas import (
    GetInvoiceRequest,
    UpdateInvoiceRequest,
)
from src.invoices.service import InvoiceService
from src.users.enums import SubscriptionPlanFeaturesEnum
from src.users.schemas import (
    FBRProfileResponse,
    GetFBRProfileRequest,
    GetUserPlanRequest,
    UpdateFBRProfileRequest,
)
from src.users.service import FBRProfileService, UserPlanService
from src.utils import get_user_id


class FBRInvoiceService:
    """Service utilities to validate and submit invoices with the FBR."""

    @staticmethod
    async def validate_invoice(
        auth_user: AuthUser, input_data: FBRValidationRequest
    ) -> FBRValidationResponse:
        """Validate an invoice with the FBR and persist status flags.

        Args:
            auth_user: Authenticated user including database session and profile.
            input_data: Request payload containing the invoice identifier.

        Returns:
            FBRValidationResponse: Normalized response payload for API consumers.

        Raises:
            BadRequestException: If the invoice is already validated or required
                integration checks are not satisfied.
            NotFoundException: When the invoice or related customer cannot be located.
        """

        user_plan = await UserPlanService.get_user_plan(
            auth_user, GetUserPlanRequest(user_id=auth_user.user.id)
        )

        if not user_plan.subscription_plan or (
            SubscriptionPlanFeaturesEnum.FBR_INVOICING
            not in user_plan.subscription_plan.features
        ):
            raise BadRequestException(
                message="FBR invoicing not included in plan",
                detail="Your current subscription plan does not include FBR invoicing features.",
                extra={"user_id": str(auth_user.user.id)},
            )

        sandbox_mode = input_data.sandbox_mode
        request_url = None
        match sandbox_mode:
            case True:
                request_url = get_setting("FBR_API_INVOICE_VALIDATE_SANDBOX_URL")
            case False:
                request_url = get_setting("FBR_API_INVOICE_VALIDATE_URL")
            case _:
                raise BadRequestException(
                    message="Invalid sandbox mode",
                    detail="The sandbox mode flag must be either true or false.",
                    extra={"sandbox_mode": sandbox_mode},
                )

        invoice_data = await InvoiceService.get_invoice_single_complete(
            auth_user,
            input_params=GetInvoiceRequest(id=input_data.invoice_id),
            include_tokens=True,
        )

        if invoice_data.fbr_validated:
            raise BadRequestException(
                message="Invoice already validated",
                detail="This invoice has already been validated with FBR.",
                extra={"invoice_id": str(input_data.invoice_id)},
            )

        if not invoice_data.fbr_profile.integration_validated:
            raise BadRequestException(
                message="FBR integration not validated",
                detail="Please validate the FBR integration tokens before proceeding.",
                extra={"user_id": str(auth_user.user.id)},
            )

        token = FBRInvoiceService._select_token(
            profile=invoice_data.fbr_profile,
            mode="sandbox" if sandbox_mode else "production",
        )

        payload = build_fbr_invoice(data=invoice_data)

        http_response = await send_fbr_request(
            url=request_url,
            token=token,
            payload=payload.model_dump(),
        )

        parsed = parse_fbr_response(http_response)

        # Check if validation was successful before persisting
        if not parsed.success:
            raise BadRequestException(
                message="FBR validation failed",
                detail="Invoice validation with FBR was unsuccessful.",
                extra=parsed.model_dump(),
            )

        await FBRInvoiceService._persist_validation_result(
            auth_user=auth_user,
            invoice_id=input_data.invoice_id,
        )

        return FBRValidationResponse.model_validate(parsed.model_dump())

    @staticmethod
    async def submit_invoice(
        auth_user: AuthUser, input_data: FBRSubmissionRequest
    ) -> FBRSubmissionResponse:
        """Submit a validated invoice to the FBR.

        Args:
            auth_user: Authenticated user including database session and profile.
            input_data: Request payload containing the invoice identifier.

        Returns:
            FBRSubmissionResponse: Normalized response payload for API consumers.

        Raises:
            BadRequestException: If the invoice has not been validated, was already
                submitted, or when the user's FBR profile is not ready for
                production submissions.
            NotFoundException: When the invoice or linked data cannot be found.
        """

        user_id = auth_user.user.id

        user_plan = await UserPlanService.get_user_plan(
            auth_user, GetUserPlanRequest(user_id=auth_user.user.id)
        )

        if not user_plan.subscription_plan or (
            SubscriptionPlanFeaturesEnum.FBR_INVOICING
            not in user_plan.subscription_plan.features
        ):
            raise BadRequestException(
                message="FBR invoicing not included in plan",
                detail="Your current subscription plan does not include FBR invoicing features.",
                extra={"user_id": str(auth_user.user.id)},
            )

        sandbox_mode = input_data.sandbox_mode
        request_url = None
        match sandbox_mode:
            case True:
                request_url = get_setting("FBR_API_INVOICE_SUBMIT_SANDBOX_URL")
            case False:
                request_url = get_setting("FBR_API_INVOICE_SUBMIT_URL")
            case _:
                raise BadRequestException(
                    message="Invalid sandbox mode",
                    detail="The sandbox mode flag must be either true or false.",
                    extra={"sandbox_mode": sandbox_mode},
                )

        invoice_data = await InvoiceService.get_invoice_single_complete(
            auth_user,
            input_params=GetInvoiceRequest(id=input_data.invoice_id),
            include_tokens=True,
        )

        if invoice_data.fbr_status == InvoiceFBRStatusEnum.SUBMITTED:
            raise BadRequestException(
                message="Invoice already submitted",
                detail="This invoice has already been submitted to FBR.",
                extra={"invoice_id": str(input_data.invoice_id)},
            )

        if not invoice_data.fbr_validated:
            raise BadRequestException(
                message="Invoice not validated",
                detail="This invoice has not been validated with FBR.",
                extra={"invoice_id": str(input_data.invoice_id)},
            )

        if not invoice_data.fbr_profile.integration_validated:
            raise BadRequestException(
                message="FBR integration not validated",
                detail="Please validate the FBR integration tokens before proceeding.",
                extra={"user_id": str(auth_user.user.id)},
            )

        if not invoice_data.fbr_profile.invoicing_enabled:
            raise BadRequestException(
                message="FBR production disabled",
                detail="Enable invoicing in your FBR profile settings before submission.",
                extra={"user_id": str(user_id)},
            )

        token = FBRInvoiceService._select_token(
            profile=invoice_data.fbr_profile,
            mode="sandbox" if sandbox_mode else "production",
        )

        payload = build_fbr_invoice(data=invoice_data)

        http_response = await send_fbr_request(
            url=request_url,
            token=token,
            payload=payload.model_dump(),
        )

        parsed = parse_fbr_response(http_response)

        # Check if submission was successful before persisting
        if not parsed.success or not parsed.reference:
            raise BadRequestException(
                message="FBR submission failed",
                detail="Invoice submission to FBR was unsuccessful.",
                extra=parsed.model_dump(),
            )

        await FBRInvoiceService._persist_submission_result(
            auth_user=auth_user,
            invoice_id=input_data.invoice_id,
            parsed=parsed,
        )

        return FBRSubmissionResponse.model_validate(parsed.model_dump())

    @staticmethod
    async def get_uom(
        auth_user: AuthUser, input_params: FBRUOMRequest
    ) -> FBRUOMResponse:
        """Retrieve the unit of measurement description for a given HS code.

        Args:
            auth_user: Authenticated user context including database session.
            input_params: Request parameters containing the HS code and annexure ID.

        Returns:
            FBRUOMResponse: Response payload containing the unit of measurement description.

        Raises:
            BadRequestException: If the sandbox token is missing or the FBR API returns an error.
        """

        return await get_fbr_uom(auth_user, input_params)

    @staticmethod
    def _select_token(
        profile: FBRProfileResponse, *, mode: Literal["sandbox", "production"]
    ) -> str:
        """Select the appropriate FBR token for the current operation.

        Args:
            profile: User's FBR profile information.
            production_mode: Whether the production token is mandatory.

        Returns:
            str: Authorization token to use with FBR endpoints.

        Raises:
            BadRequestException: If the required token is missing.
        """

        if mode not in ("sandbox", "production"):
            raise BadRequestException(
                message="Invalid token selection",
                detail="Mode must be either 'sandbox' or 'production'.",
                extra={"mode": mode},
            )

        if mode == "sandbox":
            token = profile.sandbox_token or profile.production_token
        else:
            token = profile.production_token

        if not token or token.strip() == "":
            raise BadRequestException(
                message="FBR token missing",
                detail="Unable to proceed because the FBR token is not configured.",
                extra={},
            )

        return token

    @staticmethod
    async def _persist_validation_result(
        auth_user: AuthUser,
        invoice_id: UUID,
    ) -> None:
        """Persist validation status updates for an invoice.

        Args:
            session: Active asynchronous SQLModel session.
            context: Invoice context containing the target invoice.
            parsed: Normalized response returned by the FBR API.
        """

        try:
            await InvoiceService.update_invoice(
                auth_user,
                UpdateInvoiceRequest(
                    id=invoice_id,
                    fbr_validated=True,
                    fbr_status=InvoiceFBRStatusEnum.VALIDATED,
                ),
            )
        except Exception as exc:
            raise InternalServerErrorException(
                message="Failed to persist FBR validation result",
                detail=str(exc),
                extra={
                    "operation": "persist_fbr_validation_result",
                    "user_id": str(auth_user.user.id),
                    "invoice_id": str(invoice_id),
                },
            ) from exc

    @staticmethod
    async def _persist_submission_result(
        auth_user: AuthUser,
        invoice_id: UUID,
        parsed: FBRParsedResponse,
    ) -> None:
        """Persist submission results, updating the invoice reference when present.

        Args:
            session: Active asynchronous SQLModel session.
            context: Invoice context containing the target invoice.
            parsed: Normalized response returned by the FBR API.
        """

        if not parsed.success:
            raise InternalServerErrorException(
                message="Cannot persist failed FBR submission result",
                detail="The FBR submission result indicates failure.",
                extra={
                    "operation": "persist_fbr_submission_result",
                    "user_id": str(auth_user.user.id),
                    "invoice_id": str(invoice_id),
                },
            )

        if not parsed.reference:
            raise InternalServerErrorException(
                message="FBR submission reference missing",
                detail="The FBR submission response did not include a reference number.",
                extra={
                    "operation": "persist_fbr_submission_result",
                    "user_id": str(auth_user.user.id),
                    "invoice_id": str(invoice_id),
                },
            )

        try:
            await InvoiceService.update_invoice(
                auth_user,
                UpdateInvoiceRequest(
                    id=invoice_id,
                    fbr_status=InvoiceFBRStatusEnum.SUBMITTED,
                    status=InvoiceStatusEnum.SENT,
                    fbr_reference=parsed.reference,
                ),
            )
        except Exception as exc:
            raise InternalServerErrorException(
                message="Failed to persist FBR submission result",
                detail=str(exc),
                extra={
                    "operation": "persist_fbr_submission_result",
                    "user_id": str(auth_user.user.id),
                    "invoice_id": str(invoice_id),
                },
            ) from exc


class FBRIntegrationService:
    """Service handling the execution of FBR sandbox integration scenarios."""

    @staticmethod
    async def run_integration(
        auth_user: AuthUser, input_data: FBRIntegrationRequest
    ) -> FBRIntegrationResponse:
        """Execute selected FBR integration scenarios concurrently.

        Args:
            auth_user: Authenticated user context containing the sandbox token.
            input_data: Request payload containing the target user and scenarios.

        Returns:
            FBRIntegrationResponse: Aggregated outcome of the executed scenarios.

        Raises:
            BadRequestException: If the sandbox token or NTN is missing for the user.
        """
        user_id = get_user_id(auth_user, input_data.user_id)

        # Verify that the user's subscription plan includes FBR integration
        user_plan = await UserPlanService.get_user_plan(
            auth_user, GetUserPlanRequest(user_id=user_id)
        )

        if not user_plan.subscription_plan:
            raise BadRequestException(
                message="No active subscription plan",
                detail="An active subscription plan is required to access FBR integration features.",
                extra={"user_id": str(user_id)},
            )

        # Check if FBR integration feature is included in the plan
        if (
            SubscriptionPlanFeaturesEnum.FBR_INTEGRATION
            not in user_plan.subscription_plan.features
        ):
            raise BadRequestException(
                message="FBR integration not included in plan",
                detail="Your current subscription plan does not include FBR integration features.",
                extra={"user_id": str(user_id)},
            )

        fbr_profile = await FBRProfileService.get_fbr_profile(
            auth_user,
            input_params=GetFBRProfileRequest(user_id=user_id),
        )
        sandbox_token = fbr_profile.sandbox_token

        if not sandbox_token:
            raise BadRequestException(
                message="Sandbox token missing",
                detail="Add a sandbox token to your FBR profile to run integration tests.",
                extra={"user_id": str(user_id)},
            )

        if not fbr_profile.national_tax_number:
            raise BadRequestException(
                message="National tax number missing",
                detail="Add your national tax number to your FBR profile to run integration tests.",
                extra={"user_id": str(user_id)},
            )

        # Generate scenario payloads with the user's NTN
        scenario_payloads = generate_scenario_payloads(
            ntn=fbr_profile.national_tax_number,
            scenarios=input_data.scenarios,
        )

        # Create async tasks for each scenario
        tasks = [
            FBRIntegrationService._execute_scenario(
                sandbox_token=sandbox_token,
                scenario_payload=scenario_payload,
            )
            for scenario_payload in scenario_payloads
        ]

        # Execute all scenarios concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        scenario_results: List[FBRIntegrationScenarioResultResponse] = []
        for scenario_payload, result in zip(scenario_payloads, results):
            if isinstance(result, Exception):
                # Handle exceptions that occurred during execution
                scenario_results.append(
                    FBRIntegrationScenarioResultResponse(
                        scenario_id=scenario_payload.scenario_id,
                        name=scenario_payload.name,
                        status="ERROR",
                        success=False,
                        message=str(result),
                        response_body={},
                    )
                )
            else:
                # Add successful result
                scenario_results.append(
                    cast(FBRIntegrationScenarioResultResponse, result)
                )

        # Calculate summary statistics
        success_count = sum(1 for item in scenario_results if item.success)
        total = len(scenario_results)
        overall_success = success_count > 0
        message = (
            f"{success_count}/{total} scenarios succeeded."
            if total
            else "No scenarios executed."
        )

        # Update the user's FBR profile to reflect integration validation
        if overall_success and not fbr_profile.integration_validated:
            try:
                _profile_update = await FBRProfileService.update_fbr_profile(
                    auth_user,
                    input_data=UpdateFBRProfileRequest(
                        user_id=user_id,
                        integration_validated=True,
                    ),
                )

            except Exception as e:
                raise InternalServerErrorException(
                    message="Failed to update FBR profile after successful integration",
                    detail=str(e),
                    extra={"user_id": str(user_id)},
                )

        return FBRIntegrationResponse(
            success=overall_success,
            message=message,
            scenarios=scenario_results,
        )

    @staticmethod
    async def _execute_scenario(
        sandbox_token: str, scenario_payload: ScenarioPayload
    ) -> FBRIntegrationScenarioResultResponse:
        """Execute a single integration scenario against the FBR sandbox.

        Args:
            sandbox_token: Bearer token authorised for sandbox integration.
            scenario_payload: Scenario object containing metadata and payload.

        Returns:
            FBRIntegrationScenarioResultResponse: Normalised scenario result.
        """
        # Send the payload to the FBR sandbox API
        response = await send_fbr_request(
            url=get_setting("FBR_API_INVOICE_SUBMIT_SANDBOX_URL"),
            token=sandbox_token,
            payload=scenario_payload.payload,
        )

        # Parse the API response
        parsed = parse_fbr_response(response)

        # Return normalised result
        return FBRIntegrationScenarioResultResponse(
            scenario_id=scenario_payload.scenario_id,
            name=scenario_payload.name,
            status=parsed.status,
            success=parsed.success,
            message=parsed.message,
            response_body=parsed.response_body or {},
        )
