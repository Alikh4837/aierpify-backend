# src\users\router.py
from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.exceptions import HTTPException

from src.dependencies import AuthenticatedUser
from src.exceptions import ERROR_RESPONSES, InternalServerErrorException
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
)
from src.users.service import (
    FBRProfileService,
    SubscriptionPlanService,
    UserNoteService,
    UserPlanService,
    UserProfileService,
)

router = APIRouter(prefix="/users", tags=["Users"], responses=ERROR_RESPONSES)


# --------------------------------------------------------------------------- #
#                            User Profile Endpoints                          #
# --------------------------------------------------------------------------- #
@router.get("/profile", response_model=GetUserProfileResponse)
async def get_user_profile(
    auth_user: AuthenticatedUser,
    input_params: GetUserProfileRequest = Query(),
) -> GetUserProfileResponse:
    """Get the user's profile (single record per user)."""
    try:
        return await UserProfileService.get_user_profile(auth_user, input_params)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to retrieve user profile",
            detail=str(e),
            extra={"operation": "get_user_profile", "user_id": str(auth_user.user.id)},
        )


@router.get("/profiles", response_model=GetUserProfilesResponse)
async def get_user_profiles(
    auth_user: AuthenticatedUser,
    input_params: GetUserProfilesRequest = Query(),
) -> GetUserProfilesResponse:
    """Get all user profiles. Admin only."""
    try:
        return await UserProfileService.get_user_profiles(auth_user, input_params)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to retrieve user profiles",
            detail=str(e),
            extra={"operation": "get_user_profiles", "user_id": str(auth_user.user.id)},
        )


@router.post("/profile", response_model=CreateUserProfileResponse)
async def create_user_profile(
    input_data: CreateUserProfileRequest, auth_user: AuthenticatedUser
) -> CreateUserProfileResponse:
    """Create a new user profile."""
    try:
        return await UserProfileService.create_user_profile(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to create user profile",
            detail=str(e),
            extra={
                "operation": "create_user_profile",
                "user_id": str(auth_user.user.id),
            },
        )


@router.patch("/profile", response_model=UpdateUserProfileResponse)
async def update_user_profile(
    input_data: UpdateUserProfileRequest,
    auth_user: AuthenticatedUser,
) -> UpdateUserProfileResponse:
    """Update the user's profile."""
    try:
        return await UserProfileService.update_user_profile(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to update user profile",
            detail=str(e),
            extra={
                "operation": "update_user_profile",
                "user_id": str(auth_user.user.id),
            },
        )


# --------------------------------------------------------------------------- #
#                             FBR Profile Endpoints                          #
# --------------------------------------------------------------------------- #
@router.get("/fbr-profile", response_model=GetFBRProfileResponse)
async def get_fbr_profile(
    auth_user: AuthenticatedUser,
    input_params: GetFBRProfileRequest = Query(),
) -> GetFBRProfileResponse:
    """Get the user's FBR profile (single record per user)."""
    try:
        return await FBRProfileService.get_fbr_profile(auth_user, input_params)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to retrieve FBR profile",
            detail=str(e),
            extra={"operation": "get_fbr_profile", "user_id": str(auth_user.user.id)},
        )


@router.post("/fbr-profile", response_model=CreateFBRProfileResponse)
async def create_fbr_profile(
    input_data: CreateFBRProfileRequest, auth_user: AuthenticatedUser
) -> CreateFBRProfileResponse:
    """Create a new FBR profile."""
    try:
        return await FBRProfileService.create_fbr_profile(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to create FBR profile",
            detail=str(e),
            extra={
                "operation": "create_fbr_profile",
                "user_id": str(auth_user.user.id),
            },
        )


@router.patch("/fbr-profile", response_model=UpdateFBRProfileResponse)
async def update_fbr_profile(
    input_data: UpdateFBRProfileRequest,
    auth_user: AuthenticatedUser,
) -> UpdateFBRProfileResponse:
    """Update the user's FBR profile. Special restrictions apply for national_tax_number."""
    try:
        return await FBRProfileService.update_fbr_profile(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to update FBR profile",
            detail=str(e),
            extra={
                "operation": "update_fbr_profile",
                "user_id": str(auth_user.user.id),
            },
        )


# --------------------------------------------------------------------------- #
#                              User Plan Endpoints                           #
# --------------------------------------------------------------------------- #
@router.get(
    "/plan",
    response_model=GetUserPlanResponse,
    tags=["Products", "Customers", "Invoices"],
)
async def get_user_plan(
    auth_user: AuthenticatedUser,
    input_params: GetUserPlanRequest = Query(),
) -> GetUserPlanResponse:
    """Get the user's subscription plan (single record per user)."""
    try:
        return await UserPlanService.get_user_plan(auth_user, input_params)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to retrieve user plan",
            detail=str(e),
            extra={"operation": "get_user_plan", "user_id": str(auth_user.user.id)},
        )


@router.get(
    "/plans",
    response_model=GetUserPlansResponse,
    tags=["Products", "Customers", "Invoices"],
)
async def get_user_plans(
    auth_user: AuthenticatedUser,
    input_params: GetUserPlansRequest = Query(),
) -> GetUserPlansResponse:
    """Get all user plans. Admin only."""
    try:
        return await UserPlanService.get_user_plans(auth_user, input_params)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to retrieve user plans",
            detail=str(e),
            extra={"operation": "get_user_plans", "user_id": str(auth_user.user.id)},
        )


@router.post("/plan", response_model=CreateUserPlanResponse)
async def create_user_plan(
    input_data: CreateUserPlanRequest, auth_user: AuthenticatedUser
) -> CreateUserPlanResponse:
    """Create a new user plan. Can only be created once per user."""
    try:
        return await UserPlanService.create_user_plan(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to create user plan",
            detail=str(e),
            extra={"operation": "create_user_plan", "user_id": str(auth_user.user.id)},
        )


@router.patch("/plan", response_model=UpdateUserPlanResponse)
async def update_user_plan(
    input_data: UpdateUserPlanRequest,
    auth_user: AuthenticatedUser,
) -> UpdateUserPlanResponse:
    """Update a user's plan. Only admins can update user plans."""
    try:
        return await UserPlanService.update_user_plan(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to update user plan",
            detail=str(e),
            extra={
                "operation": "update_user_plan",
                "user_id": str(auth_user.user.id),
            },
        )


@router.post("/plan/renew", response_model=UpdateUserPlanResponse)
async def renew_user_plan(
    input_data: UpdateUserPlanRequest,
    auth_user: AuthenticatedUser,
) -> UpdateUserPlanResponse:
    """Manually trigger a renewal of the user's subscription plan. Only applicable for paid plans that have expired but are set to auto-renew."""
    try:
        return await UserPlanService.renew_user_plan_by_admin(
            auth_user,
            input_data,
        )

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to renew user plan",
            detail=str(e),
            extra={
                "operation": "renew_user_plan",
                "user_id": str(auth_user.user.id),
                "target_user_id": str(input_data.user_id),
            },
        )


# --------------------------------------------------------------------------- #
#                          Subscription Plan Endpoints                       #
# --------------------------------------------------------------------------- #
@router.get("/subscription-plans", response_model=List[GetSubscriptionPlanResponse])
async def get_subscription_plans(
    auth_user: AuthenticatedUser,
    input_params: GetSubscriptionPlanRequest = Query(),
) -> List[GetSubscriptionPlanResponse]:
    """Get all subscription plans (no pagination needed)."""
    try:
        return await SubscriptionPlanService.get_subscription_plans(
            auth_user, input_params
        )

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to retrieve subscription plans",
            detail=str(e),
            extra={
                "operation": "get_subscription_plans",
                "user_id": str(auth_user.user.id),
            },
        )


@router.post("/subscription-plans", response_model=CreateSubscriptionPlanResponse)
async def create_subscription_plan(
    input_data: CreateSubscriptionPlanRequest, auth_user: AuthenticatedUser
) -> CreateSubscriptionPlanResponse:
    """Create a new subscription plan. Only admins can create plans."""
    try:
        return await SubscriptionPlanService.create_subscription_plan(
            auth_user, input_data
        )

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to create subscription plan",
            detail=str(e),
            extra={
                "operation": "create_subscription_plan",
                "user_id": str(auth_user.user.id),
            },
        )


@router.patch("/subscription-plans", response_model=UpdateSubscriptionPlanResponse)
async def update_subscription_plan(
    input_data: UpdateSubscriptionPlanRequest,
    auth_user: AuthenticatedUser,
) -> UpdateSubscriptionPlanResponse:
    """Update an existing subscription plan. Only admins can update plans."""
    try:
        return await SubscriptionPlanService.update_subscription_plan(
            auth_user, input_data
        )

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to update subscription plan",
            detail=str(e),
            extra={
                "operation": "update_subscription_plan",
                "user_id": str(auth_user.user.id),
            },
        )


@router.delete("/subscription-plans", response_model=DeleteSubscriptionPlanResponse)
async def delete_subscription_plans(
    input_data: DeleteSubscriptionPlanRequest, auth_user: AuthenticatedUser
) -> DeleteSubscriptionPlanResponse:
    """Delete subscription plans. Only admins can delete plans. Cannot delete if users are still using the plan."""
    try:
        return await SubscriptionPlanService.delete_subscription_plans(
            auth_user, input_data
        )

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to delete subscription plans",
            detail=str(e),
            extra={
                "operation": "delete_subscription_plans",
                "user_id": str(auth_user.user.id),
            },
        )


# ---------------------------- User Note Endpoints --------------------------- #
@router.get("/note/{note_id}", response_model=GetUserNoteResponse)
async def get_user_note(
    note_id: UUID,
    auth_user: AuthenticatedUser,
) -> GetUserNoteResponse:
    """Get a single user note by its ID."""
    try:
        return await UserNoteService.get_user_note(
            auth_user, GetUserNoteRequest(id=note_id)
        )

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to retrieve user note",
            detail=str(e),
            extra={
                "operation": "get_user_note",
                "user_id": str(auth_user.user.id),
                "note_id": note_id,
            },
        )


@router.get("/notes", response_model=GetUserNotesResponse)
async def get_user_notes(
    auth_user: AuthenticatedUser,
    input_params: GetUserNotesRequest = Query(),
) -> GetUserNotesResponse:
    """Get all user notes with pagination."""
    try:
        return await UserNoteService.get_user_notes(auth_user, input_params)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to retrieve user notes",
            detail=str(e),
            extra={"operation": "get_user_notes", "user_id": str(auth_user.user.id)},
        )


@router.post("/notes", response_model=CreateUserPlanResponse)
async def create_user_note(
    input_data: CreateUserNoteRequest, auth_user: AuthenticatedUser
) -> CreateUserNoteResponse:
    """Create a new user note."""
    try:
        return await UserNoteService.create_user_note(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to create user note",
            detail=str(e),
            extra={"operation": "create_user_note", "user_id": str(auth_user.user.id)},
        )


@router.patch("/notes", response_model=UpdateUserNoteResponse)
async def update_user_note(
    input_data: UpdateUserNoteRequest, auth_user: AuthenticatedUser
) -> UpdateUserNoteResponse:
    """Update an existing user note."""
    try:
        return await UserNoteService.update_user_note(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to update user note",
            detail=str(e),
            extra={"operation": "update_user_note", "user_id": str(auth_user.user.id)},
        )
