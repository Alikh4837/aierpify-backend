# src\users\service.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Sequence

from dateutil.relativedelta import relativedelta
from sqlmodel import and_, col, desc, select, update

from src.auth.models import User
from src.auth.user import AuthUser
from src.exceptions import (
    BadRequestException,
    InternalServerErrorException,
    NotFoundException,
)
from src.users.constants import DEFAULT_SUBSCRIPTION_PLAN_ID
from src.users.enums import SubscriptionPlanPeriodEnum
from src.users.models import (
    FBRProfile,
    SubscriptionPlan,
    UserNote,
    UserPlan,
    UserProfile,
)
from src.users.schemas import (
    CreateFBRProfileRequest,
    CreateFBRProfileResponse,
    CreateSubscriptionPlanRequest,
    CreateSubscriptionPlanResponse,
    CreateUserNoteRequest,
    CreateUserNoteResponse,
    CreateUserPlanRequest,
    CreateUserPlanResponse,
    CreateUserProfileRequest,
    CreateUserProfileResponse,
    DeleteSubscriptionPlanRequest,
    DeleteSubscriptionPlanResponse,
    DeleteUserNoteRequest,
    DeleteUserNoteResponse,
    GetFBRProfileRequest,
    GetFBRProfileResponse,
    GetSubscriptionPlanRequest,
    GetSubscriptionPlanResponse,
    GetUserNoteRequest,
    GetUserNoteResponse,
    GetUserNotesRequest,
    GetUserNotesResponse,
    GetUserPlanRequest,
    GetUserPlanResponse,
    GetUserPlansRequest,
    GetUserPlansResponse,
    GetUserProfileRequest,
    GetUserProfileResponse,
    GetUserProfilesRequest,
    GetUserProfilesResponse,
    SubscriptionPlanResponse,
    UpdateFBRProfileRequest,
    UpdateFBRProfileResponse,
    UpdateSubscriptionPlanRequest,
    UpdateSubscriptionPlanResponse,
    UpdateUserNoteRequest,
    UpdateUserNoteResponse,
    UpdateUserPlanRequest,
    UpdateUserPlanResponse,
    UpdateUserProfileRequest,
    UpdateUserProfileResponse,
    UserPlanResponse,
)
from src.utils import enforce_user_role, get_user_id


# --------------------------------------------------------------------------- #
#                               CRUD Services                                 #
# --------------------------------------------------------------------------- #
class UserProfileService:
    @staticmethod
    async def get_user_profile(
        auth_user: AuthUser, input_params: GetUserProfileRequest
    ) -> GetUserProfileResponse:
        """
        Retrieve the user's profile (single record per user).

        Args:
            auth_user: Authenticated user context containing DB session.
            input_params: Request parameters.

        Returns:
            GetUserProfileResponse: User profile data.
        """
        session = auth_user.session
        user_id = get_user_id(auth_user, input_params.user_id)

        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await session.exec(stmt)
        profile = result.first()

        if not profile:
            try:
                # Auto-create profile if not found
                profile = UserProfile(
                    user_id=auth_user.user.id,
                    name=auth_user.user.name,
                    email=auth_user.user.email,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(profile)
                await session.commit()
                await session.refresh(profile)

            except Exception as e:
                raise InternalServerErrorException(
                    message="Failed to create user profile", extra={"error": str(e)}
                )

        if not profile:
            raise NotFoundException(
                message="User profile not found",
                detail=f"No profile found for user ID {user_id}",
                extra={"user_id": str(user_id)},
            )

        return GetUserProfileResponse.model_validate(profile.model_dump())

    @staticmethod
    async def get_user_profiles(
        auth_user: AuthUser, input_params: GetUserProfilesRequest
    ) -> GetUserProfilesResponse:
        """
        Retrieve all user profiles. Admin only.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_params: Request parameters.

        Returns:
            GetUserProfilesResponse: List of user profile data.
        """

        enforce_user_role(auth_user, "admin")

        session = auth_user.session

        # Fetch all user IDs
        users_result = await session.exec(select(User))
        users = users_result.all()

        # TODO: Disabled fetching logo_url due to performance issues with large data sets.
        # TODO: Implement S3 based storage in future to optimize performance.
        stmt = select(
            UserProfile.id,
            UserProfile.user_id,
            UserProfile.name,
            UserProfile.email,
            UserProfile.phone,
            UserProfile.address,
            UserProfile.province,
            UserProfile.created_at,
            UserProfile.updated_at,
        )  # type: ignore

        if input_params.id:
            stmt = stmt.where(UserProfile.id == input_params.id)

        if input_params.user_id:
            stmt = stmt.where(UserProfile.user_id == input_params.user_id)

        result = await session.exec(stmt)
        profiles: Sequence[UserProfile] = result.all()

        # Check if all users have profiles, if not create missing profiles
        existing_user_ids = {profile.user_id for profile in profiles}
        missing_user_ids = {user.id for user in users} - existing_user_ids

        for missing_user_id in missing_user_ids:
            selected_user = next(
                (user for user in users if user.id == missing_user_id), None
            )
            if not selected_user:
                # This should never happen since we fetched all users at the beginning, but we add this check for safety
                raise InternalServerErrorException(
                    message="User data inconsistency",
                    detail=f"User with ID {missing_user_id} not found in users table",
                    extra={"user_id": str(missing_user_id)},
                )

            await UserProfileService.create_user_profile(
                auth_user,
                CreateUserProfileRequest(
                    user_id=selected_user.id,
                    name=selected_user.name,
                    email=selected_user.email,
                    phone="",
                    address="",
                ),
            )

            # Refetch profiles after creating missing ones
            result = await session.exec(stmt)
            profiles = result.all()

        return GetUserProfilesResponse(
            data=[
                GetUserProfileResponse.model_validate(profile) for profile in profiles
            ]
        )

    @staticmethod
    async def create_user_profile(
        auth_user: AuthUser, input_data: CreateUserProfileRequest
    ) -> CreateUserProfileResponse:
        """
        Create a new user profile.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_data: User profile creation data.
        """
        session = auth_user.session
        user_id = get_user_id(auth_user, input_data.user_id)

        # Check if profile already exists
        existing_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        existing_result = await session.exec(existing_stmt)
        if existing_result.first():
            raise BadRequestException(
                message="User profile already exists",
                detail=f"Profile already exists for user ID {user_id}",
                extra={"user_id": str(user_id)},
            )

        # Prepare payload
        payload = input_data.model_dump()
        payload["user_id"] = user_id

        profile = UserProfile(**payload)
        session.add(profile)
        await session.commit()
        await session.refresh(profile)

        return CreateUserProfileResponse.model_validate(profile.model_dump())

    @staticmethod
    async def update_user_profile(
        auth_user: AuthUser, input_data: UpdateUserProfileRequest
    ) -> UpdateUserProfileResponse:
        """
        Update an existing user profile.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_data: User profile update data.
        """
        session = auth_user.session
        user_id = get_user_id(auth_user, input_data.user_id)

        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await session.exec(stmt)
        profile = result.first()

        if not profile:
            raise NotFoundException(
                message="User profile not found",
                detail=f"No profile found for user ID {user_id}",
                extra={"user_id": str(user_id)},
            )

        profile_fields = UserProfile.model_fields.keys()
        for field in profile_fields:
            value = getattr(input_data, field, None)
            if value is not None:
                setattr(profile, field, value)

        session.add(profile)
        await session.commit()
        await session.refresh(profile)

        return UpdateUserProfileResponse.model_validate(profile.model_dump())


class FBRProfileService:
    @staticmethod
    async def get_fbr_profile(
        auth_user: AuthUser, input_params: GetFBRProfileRequest
    ) -> GetFBRProfileResponse:
        """
        Retrieve the user's FBR profile (single record per user).

        Args:
            auth_user: Authenticated user context containing DB session.
            input_params: Request parameters.

        Returns:
            GetFBRProfileResponse: FBR profile data.
        """
        session = auth_user.session
        user_id = get_user_id(auth_user, input_params.user_id)

        stmt = select(FBRProfile).where(FBRProfile.user_id == user_id)
        result = await session.exec(stmt)
        profile = result.first()

        if not profile:
            new_profile = await FBRProfileService.create_fbr_profile(
                auth_user,
                CreateFBRProfileRequest(
                    user_id=user_id, sandbox_token="", production_token=""
                ),
                override_admin_check=True,
            )

            if not new_profile:
                raise NotFoundException(
                    message="FBR profile not found",
                    detail=f"No FBR profile found for user ID {user_id}",
                    extra={"user_id": str(user_id)},
                )

            else:
                profile = FBRProfile(**new_profile.model_dump())

        return GetFBRProfileResponse.model_validate(profile.model_dump())

    @staticmethod
    async def create_fbr_profile(
        auth_user: AuthUser,
        input_data: CreateFBRProfileRequest,
        override_admin_check: bool = False,
    ) -> CreateFBRProfileResponse:
        """
        Create a new FBR profile.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_data: FBR profile creation data.
        """
        session = auth_user.session
        if not override_admin_check:
            user_id = get_user_id(auth_user, input_data.user_id)
        else:
            user_id = auth_user.user.id

        # Check if profile already exists
        existing_stmt = select(FBRProfile).where(FBRProfile.user_id == user_id)
        existing_result = await session.exec(existing_stmt)
        if existing_result.first():
            raise BadRequestException(
                message="FBR profile already exists",
                detail=f"FBR profile already exists for user ID {user_id}",
                extra={"user_id": str(user_id)},
            )

        # Prepare payload
        payload = input_data.model_dump()
        payload["user_id"] = user_id

        profile = FBRProfile(**payload)
        session.add(profile)
        await session.commit()
        await session.refresh(profile)

        return CreateFBRProfileResponse.model_validate(profile.model_dump())

    @staticmethod
    async def update_fbr_profile(
        auth_user: AuthUser, input_data: UpdateFBRProfileRequest
    ) -> UpdateFBRProfileResponse:
        """
        Update an existing FBR profile.

        Special restriction: regular users cannot update national_tax_number after it's set.
        Only admins can update it.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_data: FBR profile update data.
        """
        session = auth_user.session
        user_id = get_user_id(auth_user, input_data.user_id)

        stmt = select(FBRProfile).where(FBRProfile.user_id == user_id)
        result = await session.exec(stmt)
        profile = result.first()

        if not profile:
            raise NotFoundException(
                message="FBR profile not found",
                detail=f"No FBR profile found for user ID {user_id}",
                extra={"user_id": str(user_id)},
            )

        # Check if regular user is trying to update national_tax_number after it has a value
        if (
            input_data.national_tax_number is not None
            and profile.national_tax_number not in (None, "")
            and input_data.national_tax_number != profile.national_tax_number
        ):
            # Enforce admin role for national_tax_number updates
            enforce_user_role(
                auth_user, "admin", "Forbidden to update national_tax_number"
            )

        profile_fields = FBRProfile.model_fields.keys()
        for field in profile_fields:
            value = getattr(input_data, field, None)
            if value is not None:
                setattr(profile, field, value)

        session.add(profile)
        await session.commit()
        await session.refresh(profile)

        return UpdateFBRProfileResponse.model_validate(profile.model_dump())


class UserPlanService:
    @staticmethod
    async def get_user_plan(
        auth_user: AuthUser, input_params: GetUserPlanRequest
    ) -> GetUserPlanResponse:
        """
        Retrieve the user's plan (single record per user).
        If no plan is found, a default plan is created.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_params: Request parameters.

        Returns:
            GetUserPlanResponse: User plan data with linked subscription plan.
        """
        session = auth_user.session

        user_id = get_user_id(auth_user, input_params.user_id)

        stmt = (
            select(UserPlan, SubscriptionPlan)
            .where(UserPlan.user_id == user_id)
            .join(SubscriptionPlan, col(SubscriptionPlan.id) == UserPlan.plan_id)
        )

        if input_params.id:
            stmt = stmt.where(UserPlan.id == input_params.id)

        result = await session.exec(stmt)
        row = result.first()

        plan: UserPlan
        subscription_plan: SubscriptionPlan

        if row is not None:
            plan, subscription_plan = row

            # Check plan validity and handle expiration/usage reset
            await UserPlanService.check_plan_validity(
                auth_user, plan, subscription_plan
            )

            # Refresh plan after potential updates
            await session.refresh(plan)

        else:
            # If no plan found, create the default plan
            if input_params.id is not None:
                # If searching by id and it's not found, it's a NotFoundException
                raise NotFoundException(
                    message="User plan not found",
                    detail=f"No plan found with ID {input_params.id}",
                    extra={"id": str(input_params.id)},
                )

            # Create default plan for user_id
            created_plan_response = await UserPlanService.create_user_plan(
                auth_user,
                CreateUserPlanRequest(
                    user_id=user_id, plan_id=DEFAULT_SUBSCRIPTION_PLAN_ID
                ),
                override_admin_check=True,
            )

            # Extract models from the response
            plan = UserPlan.model_validate(
                created_plan_response.model_dump(exclude={"subscription_plan"})
            )
            subscription_plan = SubscriptionPlan.model_validate(
                created_plan_response.subscription_plan.model_dump()
            )

        # Return the plan (existing or newly created)
        return GetUserPlanResponse(
            **plan.model_dump(),
            subscription_plan=SubscriptionPlanResponse.model_validate(
                subscription_plan.model_dump()
            ),
        )

    @staticmethod
    async def get_user_plans(
        auth_user: AuthUser, input_params: GetUserPlansRequest
    ) -> GetUserPlansResponse:
        """
        Retrieve all user plans. Admin only.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_params: Request parameters.

        Returns:
            GetUserPlansResponse: List of user plan data.
        """

        enforce_user_role(auth_user, "admin")

        session = auth_user.session

        stmt = select(UserPlan)

        if input_params.id:
            stmt = stmt.where(UserPlan.id == input_params.id)

        if input_params.user_id:
            stmt = stmt.where(UserPlan.user_id == input_params.user_id)

        result = await session.exec(stmt)

        plans = result.all()

        return GetUserPlansResponse(
            data=[UserPlanResponse.model_validate(plan.model_dump()) for plan in plans]
        )

    @staticmethod
    async def create_user_plan(
        auth_user: AuthUser,
        input_data: CreateUserPlanRequest,
        override_admin_check: bool = False,
    ) -> CreateUserPlanResponse:
        """
        Create a new user plan. Can only be created once per user.
        Enforces admin role if any field other than user_id is provided.
        If no plan_id is provided, the DEFAULT_SUBSCRIPTION_PLAN_ID is used.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_data: User plan creation data.
        """
        session = auth_user.session
        user_id = auth_user.user.id

        # Determine if admin role is needed
        if override_admin_check:
            requires_admin = False
        else:
            requires_admin = any(
                getattr(input_data, field) is not None
                for field in CreateUserPlanRequest.model_fields.keys()
                if field != "user_id"
            ) or (input_data.user_id is not None)

        if requires_admin:
            enforce_user_role(auth_user, "admin")

            # Get user_id. get_user_id handles ID mismatch for non-admins if user_id is provided.
            user_id = get_user_id(auth_user, input_data.user_id)

        # Check if plan already exists for this user
        existing_stmt = select(UserPlan).where(UserPlan.user_id == user_id)
        existing_result = await session.exec(existing_stmt)
        if existing_result.first():
            raise BadRequestException(
                message="User plan already exists",
                detail=f"Plan already exists for user ID {user_id}",
                extra={"user_id": str(user_id)},
            )

        # If no plan_id is provided, use default (input_data.plan_id will be None unless admin sets it, a user cannot set it)
        plan_id = input_data.plan_id or DEFAULT_SUBSCRIPTION_PLAN_ID

        # Fetch the subscription plan details
        subscription_plan_stmt = select(SubscriptionPlan).where(
            SubscriptionPlan.id == plan_id
        )
        subscription_plan_result = await session.exec(subscription_plan_stmt)
        subscription_plan = subscription_plan_result.first()

        if not subscription_plan:
            raise NotFoundException(
                message="Subscription plan not found",
                detail=f"No subscription plan found with ID {plan_id}",
                extra={"plan_id": str(plan_id)},
            )

        # Prepare payload from subscription plan (default creation) or input data (admin override)
        payload = input_data.model_dump(exclude_none=True)
        payload["user_id"] = user_id
        payload["plan_id"] = plan_id
        payload["start_date"] = datetime.now(timezone.utc)

        plan = UserPlan(**payload)
        session.add(plan)
        await session.commit()
        await session.refresh(plan)

        return CreateUserPlanResponse(
            **plan.model_dump(),
            subscription_plan=SubscriptionPlanResponse.model_validate(
                subscription_plan.model_dump()
            ),
        )

    @staticmethod
    async def update_user_plan(
        auth_user: AuthUser, input_data: UpdateUserPlanRequest
    ) -> UpdateUserPlanResponse:
        """
        Update an existing user plan. Only admins can update user plans.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_data: User plan update data.
        """
        # Enforce admin role for updates
        enforce_user_role(auth_user, "admin")

        session = auth_user.session
        user_id = get_user_id(auth_user, input_data.user_id)

        stmt = select(UserPlan).where(UserPlan.user_id == user_id)
        result = await session.exec(stmt)
        plan = result.first()

        if not plan:
            raise NotFoundException(
                message="User plan not found",
                detail=f"No plan found for user ID {user_id}",
                extra={"user_id": str(user_id)},
            )

        if input_data.plan_id:
            plan.plan_id = input_data.plan_id
        if input_data.products_used is not None:
            plan.products_used = input_data.products_used
        if input_data.customers_used is not None:
            plan.customers_used = input_data.customers_used
        if input_data.invoices_used is not None:
            plan.invoices_used = input_data.invoices_used
        if input_data.start_date is not None:
            plan.start_date = input_data.start_date
        if input_data.auto_renew is not None:
            plan.auto_renew = input_data.auto_renew

        session.add(plan)
        await session.commit()
        await session.refresh(plan)

        return UpdateUserPlanResponse.model_validate(plan.model_dump())

    @staticmethod
    async def renew_user_plan_by_admin(
        auth_user: AuthUser, input_data: UpdateUserPlanRequest
    ) -> UpdateUserPlanResponse:
        """
        Renew a user's plan starting from the current date. Admin only.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_data: User plan update data.

        Returns:
            UpdateUserPlanResponse: Updated plan details after renewal.
        """
        enforce_user_role(auth_user, "admin")

        session = auth_user.session

        stmt = (
            select(UserPlan, SubscriptionPlan)
            .where(UserPlan.user_id == input_data.user_id)
            .join(SubscriptionPlan, col(SubscriptionPlan.id) == UserPlan.plan_id)
        )
        result = await session.exec(stmt)
        row = result.first()

        if not row:
            raise NotFoundException(
                message="User plan not found",
                detail=f"No plan found for user ID {input_data.user_id}",
                extra={"user_id": str(input_data.user_id)},
            )

        user_plan, _subscription_plan = row

        await UserPlanService.renew_user_plan(
            auth_user,
            user_plan,
            start_date=datetime.now(tz=timezone.utc),
        )

        await session.refresh(user_plan)

        return UpdateUserPlanResponse.model_validate(user_plan.model_dump())

    @staticmethod
    async def renew_user_plan(
        auth_user: AuthUser,
        user_plan: UserPlan,
        start_date: Optional[datetime] = None,
    ) -> None:
        """
        Renew the user's plan and reset usage counters.

        Args:
            auth_user: Authenticated user context containing DB session.
            user_plan: The user's plan to renew.
            start_date: Optional start date for the renewed plan.
        """
        session = auth_user.session
        new_start_date = start_date or datetime.now(tz=timezone.utc)

        user_plan.start_date = new_start_date
        user_plan.products_used = 0
        user_plan.customers_used = 0
        user_plan.invoices_used = 0

        session.add(user_plan)
        await session.commit()

    @staticmethod
    async def check_plan_validity(
        auth_user: AuthUser, user_plan: UserPlan, subscription_plan: SubscriptionPlan
    ) -> None:
        """
        Check if the user's plan has expired or needs usage reset.
        For free plans, automatically renew when billing period expires.
        For paid plans, raise exception if billing period expires.
        Reset usage counters when usage period expires.

        Args:
            auth_user: Authenticated user context containing DB session.
            user_plan: The user's plan to check.
            subscription_plan: The associated subscription plan.

        Raises:
            BadRequestException: If a paid plan has expired.
        """
        current_utc_datetime = datetime.now(tz=timezone.utc)

        # Calculate the plan end date using the billing period
        plan_end_date = None
        match subscription_plan.billing_period:
            case SubscriptionPlanPeriodEnum.MONTHLY:
                # Add one month to start date
                plan_end_date = user_plan.start_date + relativedelta(months=1)
            case SubscriptionPlanPeriodEnum.YEARLY:
                plan_end_date = user_plan.start_date + relativedelta(years=1)

        # Check if the plan has expired, based on the billing period
        if plan_end_date and plan_end_date < current_utc_datetime:
            # Auto-renew free plans or plans with auto_renew enabled, otherwise raise exception for paid plans
            if (
                user_plan.auto_renew
                or subscription_plan.id == DEFAULT_SUBSCRIPTION_PLAN_ID
            ):
                await UserPlanService.renew_user_plan(
                    auth_user,
                    user_plan,
                    start_date=current_utc_datetime,
                )
            else:
                # Paid plan has expired, raise exception
                raise BadRequestException(
                    message="User plan has expired",
                    detail=f"The plan for user ID {user_plan.user_id} has expired on {plan_end_date.isoformat()}",
                    extra={
                        "user_id": str(user_plan.user_id),
                        "plan_end_date": plan_end_date.isoformat(),
                    },
                )

        if subscription_plan.limits_active:
            # Calculate the plan usage reset date using the usage period
            plan_usage_reset_date = None
            match subscription_plan.usage_period:
                case SubscriptionPlanPeriodEnum.MONTHLY:
                    # Add one month to start date
                    plan_usage_reset_date = user_plan.start_date + relativedelta(
                        months=1
                    )
                case SubscriptionPlanPeriodEnum.YEARLY:
                    # Add one year to start date
                    plan_usage_reset_date = user_plan.start_date + relativedelta(
                        years=1
                    )

            # Check if usage period has expired and reset usage counters
            if plan_usage_reset_date and plan_usage_reset_date < current_utc_datetime:
                await UserPlanService.reset_user_plan_usage(
                    auth_user, user_plan, subscription_plan
                )

    @staticmethod
    async def reset_user_plan_usage(
        auth_user: AuthUser,
        user_plan: Optional[UserPlan] = None,
        subscription_plan: Optional[SubscriptionPlan] = None,
    ) -> None:
        """
        Reset the usage counters for a user's plan.
        This is called when the usage period has expired.

        Args:
            auth_user: Authenticated user context containing DB session.
            user_plan: The user's plan to reset (optional).
            subscription_plan: The associated subscription plan (optional).
        """
        session = auth_user.session

        if user_plan is None:
            # If no plan provided, fetch the current user's plan
            user_id = auth_user.user.id
            stmt = select(UserPlan).where(UserPlan.user_id == user_id)
            result = await session.exec(stmt)
            user_plan = result.first()

            if not user_plan:
                raise NotFoundException(
                    message="User plan not found",
                    detail=f"No plan found for user ID {user_id}",
                    extra={"user_id": str(user_id)},
                )

        # Reset usage counters (UserPlan)
        user_plan.products_used = 0
        user_plan.customers_used = 0
        user_plan.invoices_used = 0

        # Calculate new start date based on usage period
        if subscription_plan:
            match subscription_plan.usage_period:
                case SubscriptionPlanPeriodEnum.MONTHLY:
                    # Set to the beginning of current month or the expected reset date
                    user_plan.start_date = user_plan.start_date + relativedelta(
                        months=1
                    )
                case SubscriptionPlanPeriodEnum.YEARLY:
                    user_plan.start_date = user_plan.start_date + relativedelta(years=1)

        session.add(user_plan)
        await session.commit()

    @staticmethod
    async def increment_usage_counter(
        auth_user: AuthUser, counter_field: str, increment_by: int = 1
    ) -> None:
        """
        Atomically increment a specific usage counter for the user's plan.
        Checks against limits defined in the SubscriptionPlan table.
        Only increments if the new value won't exceed the plan's limit.
        """
        session = auth_user.session
        user_id = auth_user.user.id

        # Validate that the field exists on UserPlan model
        if not hasattr(UserPlan, counter_field):
            raise BadRequestException(
                message="Invalid usage counter field",
                detail=f"The field '{counter_field}' does not exist on UserPlan",
                extra={"field": counter_field},
            )

        # Derive the limit field name from counter field
        # e.g., products_used -> products_limit
        limit_field = counter_field.replace("_used", "_limit")

        if not hasattr(SubscriptionPlan, limit_field):
            raise BadRequestException(
                message="Invalid limit field",
                detail=f"The limit field '{limit_field}' does not exist on SubscriptionPlan",
                extra={"field": limit_field},
            )

        # Get the column attributes
        counter_column = getattr(UserPlan, counter_field)
        limit_column = getattr(SubscriptionPlan, limit_field)

        # Perform conditional atomic update with JOIN
        # This UPDATE only executes if the new value won't exceed the limit from SubscriptionPlan
        # Also check if the SubscriptionPlan.limits_active is True, if not then skip the limit check
        stmt = (
            update(UserPlan)
            .where(
                and_(
                    UserPlan.user_id == user_id,
                    UserPlan.plan_id == SubscriptionPlan.id,  # JOIN condition
                    SubscriptionPlan.limits_active,  # Limits must be active
                    counter_column + increment_by <= limit_column,  # Limit check
                )
            )
            .values({counter_field: counter_column + increment_by})
        )

        result = await session.exec(stmt)

        # Check if any rows were updated
        if result.rowcount == 0:
            # Either user plan doesn't exist or limit would be exceeded
            # Or limits are not active
            # Fetch details to provide a better error message
            check_stmt = (
                select(UserPlan, SubscriptionPlan)
                .where(UserPlan.user_id == user_id)
                .join(SubscriptionPlan, col(SubscriptionPlan.id) == UserPlan.plan_id)
            )
            check_result = await session.exec(check_stmt)
            row = check_result.first()

            if not row:
                raise NotFoundException(
                    message="User plan not found",
                    detail=f"No plan found for user ID {user_id}",
                    extra={"user_id": str(user_id)},
                )

            user_plan, subscription_plan = row
            if not subscription_plan.limits_active:
                # If limits are not active, no need to raise limit exceeded error
                return

            current_value = getattr(user_plan, counter_field)
            limit_value = getattr(subscription_plan, limit_field)

            raise BadRequestException(
                message="Usage limit exceeded",
                detail=f"Cannot create resource. You've reached your plan limit for {counter_field.replace('_used', '')}.",
                extra={
                    "field": counter_field,
                    "current": current_value,
                    "limit": limit_value,
                    "would_be": current_value + increment_by,
                    "plan_name": subscription_plan.name
                    if hasattr(subscription_plan, "name")
                    else None,
                    "user_id": str(user_id),
                },
            )


class SubscriptionPlanService:
    @staticmethod
    async def get_subscription_plans(
        auth_user: AuthUser, input_params: GetSubscriptionPlanRequest
    ) -> List[GetSubscriptionPlanResponse]:
        """
        Retrieve all subscription plans (no pagination needed).

        Args:
            auth_user: Authenticated user context containing DB session.
            input_params: Request parameters.

        Returns:
            List[GetSubscriptionPlanResponse]: List of subscription plans.
        """

        # Enforce admin role to view all plans
        enforce_user_role(auth_user, "admin")
        session = auth_user.session

        if input_params.id:
            # Get specific plan by ID
            stmt = select(SubscriptionPlan).where(
                SubscriptionPlan.id == input_params.id
            )
            result = await session.exec(stmt)
            plan = result.first()

            if not plan:
                raise NotFoundException(
                    message="Subscription plan not found",
                    detail=f"No plan found with ID {input_params.id}",
                    extra={"plan_id": str(input_params.id)},
                )

            return [GetSubscriptionPlanResponse.model_validate(plan.model_dump())]
        else:
            # Get all plans
            stmt = select(SubscriptionPlan)
            result = await session.exec(stmt)
            plans = result.all()

            return [
                GetSubscriptionPlanResponse.model_validate(p.model_dump())
                for p in plans
            ]

    @staticmethod
    async def create_subscription_plan(
        auth_user: AuthUser, input_data: CreateSubscriptionPlanRequest
    ) -> CreateSubscriptionPlanResponse:
        """
        Create a new subscription plan. Only admins can create plans.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_data: Subscription plan creation data.
        """
        # Enforce admin role
        enforce_user_role(auth_user, "admin")

        session = auth_user.session

        # Prepare payload
        payload = input_data.model_dump()

        plan = SubscriptionPlan(**payload)
        session.add(plan)
        await session.commit()
        await session.refresh(plan)

        return CreateSubscriptionPlanResponse.model_validate(plan.model_dump())

    @staticmethod
    async def update_subscription_plan(
        auth_user: AuthUser, input_data: UpdateSubscriptionPlanRequest
    ) -> UpdateSubscriptionPlanResponse:
        """
        Update an existing subscription plan. Only admins can update plans.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_data: Subscription plan update data.
        """
        # Enforce admin role
        enforce_user_role(auth_user, "admin")

        session = auth_user.session

        stmt = select(SubscriptionPlan).where(SubscriptionPlan.id == input_data.id)
        result = await session.exec(stmt)
        plan = result.first()

        if not plan:
            raise NotFoundException(
                message="Subscription plan not found",
                detail=f"No plan found with ID {input_data.id}",
                extra={"plan_id": str(input_data.id)},
            )

        plan_fields = SubscriptionPlan.model_fields.keys()
        for field in plan_fields:
            value = getattr(input_data, field, None)
            if value is not None:
                setattr(plan, field, value)

        session.add(plan)
        await session.commit()
        await session.refresh(plan)

        return UpdateSubscriptionPlanResponse.model_validate(plan.model_dump())

    @staticmethod
    async def delete_subscription_plans(
        auth_user: AuthUser, input_data: DeleteSubscriptionPlanRequest
    ) -> DeleteSubscriptionPlanResponse:
        """
        Delete subscription plans. Only admins can delete plans.
        Cannot delete if any users are still using the plan.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_data: Subscription plan deletion data.
        """
        # Enforce admin role
        enforce_user_role(auth_user, "admin")

        session = auth_user.session
        ids = input_data.id

        if not ids:
            return DeleteSubscriptionPlanResponse(
                message="No subscription plans specified for deletion",
                detail={"deleted": 0},
            )

        # Check for users still using these plans
        user_plans_stmt = select(UserPlan).where(col(UserPlan.plan_id).in_(ids))
        user_plans_result = await session.exec(user_plans_stmt)
        active_user_plans = list(user_plans_result.all())

        if active_user_plans:
            # Return the user plans that are still using these plans
            user_plan_details = [
                {
                    "user_id": str(up.user_id),
                    "plan_id": str(up.plan_id),
                    "id": str(up.id),
                }
                for up in active_user_plans
            ]
            raise BadRequestException(
                message="Cannot delete subscription plans with active users",
                detail="One or more plans are still being used by users",
                extra={
                    "active_user_plans": user_plan_details,
                    "total_active_users": len(active_user_plans),
                },
            )

        # Fetch plans to delete
        plans_stmt = select(SubscriptionPlan).where(col(SubscriptionPlan.id).in_(ids))
        plans_result = await session.exec(plans_stmt)
        plans = list(plans_result.all())

        # Check existence
        found_ids = {p.id for p in plans}
        missing_ids = [str(i) for i in ids if i not in found_ids]

        if missing_ids:
            raise NotFoundException(
                message="Some subscription plans not found",
                detail="One or more plan IDs do not exist",
                extra={"missing_ids": missing_ids},
            )

        # Delete plans
        for plan in plans:
            await session.delete(plan)

        await session.commit()

        return DeleteSubscriptionPlanResponse(
            message=f"Deleted {len(plans)} subscription plans successfully",
            detail={"deleted": len(plans), "ids": [str(p.id) for p in plans]},
        )


class UserNoteService:
    @staticmethod
    async def create_user_note(
        auth_user: AuthUser, input_data: CreateUserNoteRequest
    ) -> CreateUserNoteResponse:
        """
        Create a new user note.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_data: User note creation data.

        Returns:
            CreateUserNoteResponse: Created user note data.
        """
        session = auth_user.session
        user_id = get_user_id(auth_user, input_data.user_id)

        input_data.user_id = user_id

        # If setting this note as default, unset any existing default note
        if input_data.default and input_data.default is True:
            default_note = await UserNoteService.get_default_note(auth_user)

            if default_note:
                # Update the default note to not be default anymore
                default_note.default = False
                session.add(default_note)
                await session.commit()

        user_note = UserNote(**input_data.model_dump())
        session.add(user_note)
        await session.commit()
        await session.refresh(user_note)

        return CreateUserNoteResponse.model_validate(user_note.model_dump())

    @staticmethod
    async def get_user_note(
        auth_user: AuthUser, input_params: GetUserNoteRequest
    ) -> GetUserNoteResponse:
        """
        Retrieve all notes for a given user.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_params: Request parameters including user_id.

        Returns:
            GetUserNoteResponse: Single user note.
        """

        session = auth_user.session
        user_id = get_user_id(auth_user, input_params.user_id)

        if not input_params.id:
            raise BadRequestException(
                message="Note ID is required",
                detail="Please provide a valid note ID to retrieve the note",
            )

        stmt = select(UserNote).where(
            UserNote.id == input_params.id, UserNote.user_id == user_id
        )
        result = await session.exec(stmt)
        note = result.first()

        if not note:
            raise NotFoundException(
                message="User note not found",
                detail=f"No note found with ID {input_params.id} for user ID {user_id}",
                extra={
                    "note_id": str(input_params.id),
                    "user_id": str(user_id),
                },
            )

        return GetUserNoteResponse.model_validate(note.model_dump())

    @staticmethod
    async def get_default_note(auth_user: AuthUser) -> Optional[UserNote]:
        """
        Find and return the default note for the authenticated user.

        Args:
            auth_user: Authenticated user context containing DB session.

        Returns:
            Optional[UserNote]: The default user note if found.
        """

        session = auth_user.session
        user_id = get_user_id(auth_user)

        stmt = select(UserNote).where(UserNote.user_id == user_id, UserNote.default)
        result = await session.exec(stmt)
        note = result.first()

        return note

    @staticmethod
    async def update_user_note(
        auth_user: AuthUser, input_data: UpdateUserNoteRequest
    ) -> UpdateUserNoteResponse:
        """
        Update an existing user note.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_data: User note update data.

        Returns:
            CreateUserNoteResponse: Updated user note data.
        """
        session = auth_user.session
        user_id = get_user_id(auth_user, input_data.user_id)

        stmt = select(UserNote).where(
            UserNote.id == input_data.id, UserNote.user_id == user_id
        )
        result = await session.exec(stmt)
        note = result.first()

        if not note:
            raise NotFoundException(
                message="User note not found",
                detail=f"No note found with ID {input_data.id} for user ID {user_id}",
                extra={
                    "note_id": str(input_data.id),
                    "user_id": str(user_id),
                },
            )

        # If setting this note as default, unset any existing default note
        if input_data.default and input_data.default is True:
            default_note = await UserNoteService.get_default_note(auth_user)

            if default_note:
                # Update the default note to not be default anymore
                default_note.default = False
                session.add(default_note)
                await session.commit()

        note_fields = UserNote.model_fields.keys()
        for field in note_fields:
            value = getattr(input_data, field, None)
            if value is not None:
                setattr(note, field, value)

        session.add(note)
        await session.commit()
        await session.refresh(note)

        return UpdateUserNoteResponse.model_validate(note.model_dump())

    @staticmethod
    async def get_user_notes(
        auth_user: AuthUser, input_params: GetUserNotesRequest
    ) -> GetUserNotesResponse:
        """
        Retrieve all notes for a given user.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_params: Request parameters including user_id.

        Returns:
            GetUserNotesResponse: List of user notes.
        """

        session = auth_user.session
        user_id = get_user_id(auth_user, input_params.user_id)

        stmt = select(UserNote).where(UserNote.user_id == user_id)

        if input_params.default is not None:
            stmt = stmt.where(UserNote.default == input_params.default)

        # Apply ordering
        stmt = stmt.order_by(desc(UserNote.created_at))

        result = await session.exec(stmt)
        notes = result.all()

        if not notes:
            raise NotFoundException(
                message="No user notes found",
                detail=f"No notes found for user ID {user_id}",
                extra={"user_id": str(user_id)},
            )

        return GetUserNotesResponse(
            data=[GetUserNoteResponse.model_validate(n.model_dump()) for n in notes]
        )

    @staticmethod
    async def delete_user_note(
        auth_user: AuthUser, input_data=DeleteUserNoteRequest
    ) -> DeleteUserNoteResponse:
        """
        Delete a user note.

        Args:
            auth_user: Authenticated user context containing DB session.
            note_id: ID of the note to delete.
            user_id: ID of the user who owns the note.
        """

        session = auth_user.session
        user_id = get_user_id(auth_user)

        stmt = select(UserNote).where(
            UserNote.id == input_data.id, UserNote.user_id == user_id
        )
        result = await session.exec(stmt)
        note = result.first()

        if not note:
            raise NotFoundException(
                message="User note not found",
                detail=f"No note found with ID {input_data.id} for user ID {user_id}",
                extra={"note_id": str(input_data.id), "user_id": str(user_id)},
            )

        await session.delete(note)
        await session.commit()

        return DeleteUserNoteResponse(
            message="User note deleted successfully",
        )
