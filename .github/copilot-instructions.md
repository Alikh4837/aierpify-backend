# Copilot Instructions - FastAPI Backend CRUD Setup

## Overview
This document provides instructions for setting up CRUD endpoints for any model in a FastAPI backend following established patterns. Use this guide to quickly scaffold new modules or extend existing ones.

## General Code Standards

### File Structure Requirements
- All files must include a file path comment at the top: `# src\module_name\submodule\file.py`
- Use absolute imports throughout: `from src.module_name.submodule import ClassName`
- All functions require proper type hinting
- All functions require Google Style docstrings

### Core Files Per Module
Each module should contain:
- `models.py` - SQLModel ORM definitions
- `schemas.py` - Input/output schemas for endpoints
- `service.py` - Business logic functions
- `router.py` - FastAPI endpoint definitions

## Schema Patterns (schemas.py)

This section defines the canonical, machine-friendly schema file format and detailed scaffolding rules so that future agentic coding runs can fully generate new schema files from a single existing Base model. Follow these rules exactly.

Important file conventions for schemas.py
- Every schema file must start with a file path comment matching the module (example at top of generated files):
  # src\module_name\schemas.py
- Use absolute imports only.
- All I/O schemas must be SQLModel classes (not plain pydantic.BaseModel) so they align with the rest of the codebase and can be used interchangeably with ORM objects.
- Use typing.List and typing.Optional where appropriate.
- Always import the shared mixins from src.schemas:
  from src.schemas import (
      DeleteResponseMixin,
      IDMixin,
      OptionalIDMixin,
      PaginatedRequestMixin,
      PaginatedResponseMixin,
      TimestampMixin,
  )

Canonical composition and naming
- Base model: <ModelName>Base(SQLModel)
  - Contains all database-relevant fields with Field(..., description="...") set exactly as in the ORM model.
  - Add __tablename__ if present in other files, keep it in Base.
  - Docstring must describe the model and include an Attributes block with each field and the exact descriptions used in Field(..., description=...).
- Response model: <ModelName>Response(<ModelName>Base, IDMixin, TimestampMixin)
  - Docstring: begins with "Response model for ..." then includes the Attributes block copied from the Base model and appends:
      created_at (datetime): Timestamp when the record was created.
      updated_at (datetime): Timestamp when the record was last updated.
  - Class body is typically pass.
- Create request: Create<ModelName>Request(<ModelName>Base)
  - Docstring begins with "Request model for creating a new <model>."
  - Mark owner/user id as Optional if needed by front-end creation flows (e.g., user_id: Optional[UUID] = Field(nullable=False, ...)).
  - Do not include auto-generated fields like id, created_at, updated_at in the docstring as required inputs; include them only in Response docstrings.
- Create response: Create<ModelName>Response(<ModelName>Response)
  - Docstring begins with "Response model for creating a new <model>."
  - Mirrors the Response model docstring exactly.
- Get request: Get<ModelName>Request(<ModelName>Base, OptionalIDMixin, PaginatedRequestMixin)
  - Docstring begins with "Request model for retrieving <plural model> with filtering and pagination."
  - Attributes block must include Base attributes (use same descriptions) and also:
      id (Optional[UUID]): Unique identifier for the record.  (Only if OptionalIDMixin is used)
      page (int): Page number for pagination.
      page_size (int): Number of records per page for pagination.
  - This class is used for list endpoints and query parameter parsing.
- Get response: Get<ModelName>Response(PaginatedResponseMixin)
  - Docstring begins with "Response model for retrieving <plural model>."
  - Attributes:
      data (list[<ModelName>Response]): List of model records.
      total (int): Total number of records available.
      next_page (bool): Indicates if there is a next page.
  - data: List[<ModelName>Response] must be declared on the class.
- Update request: Update<ModelName>Request(<ModelName>Base, OptionalIDMixin)
  - Docstring begins with "Request model for updating an existing <model>."
  - All updatable fields must be overridden as Optional with default=None and Field(..., description="...") preserving the original description text from Base.
  - id field is optional via OptionalIDMixin; include id in the docstring.
- Update response: Update<ModelName>Response(<ModelName>Response)
  - Docstring begins with "Response model for updating an existing <model>." and matches Response docstring.
- Delete response: Delete<ModelName>Response(DeleteResponseMixin)
  - Docstring begins with "Response model for deleting a <model>."
  - Attributes should be:
      message (str): Message about the deletion.
      detail (Optional[Any]): Additional detail about the deletion.

Exact docstring rules (machine-parsable)
- Every class docstring must follow this pattern:
  """
  <Top-line: Request/Response model for ...>

  Attributes:
      field1 (Type): Exact description text from Base Field(description="...").
      field2 (Optional[Type]): Exact description text from Base Field(description="...").
      ...
      created_at (datetime): Timestamp when the record was created.  # only in Response classes
      updated_at (datetime): Timestamp when the record was last updated.  # only in Response classes
  """
- The Attributes block should copy the Base Field descriptions verbatim. This enables automatic extraction/parsing by agentic scaffolding tools.
- For Create request classes, mark owner/user fields as Optional in both the signature and docstring where appropriate.

Imports and typing
- Minimal import pattern to include at top of schemas.py:
  from typing import List, Optional
  from uuid import UUID
  from sqlmodel import Field, SQLModel
  from datetime import datetime  # if any datetime fields
  from src.schemas import (DeleteResponseMixin, DeleteRequestMixin, IDMixin, OptionalIDMixin, PaginatedRequestMixin, PaginatedResponseMixin, TimestampMixin)
- Only import datetime if a field requires it. Linters should reject unused imports.

Field descriptions
- Field(..., description="...") must be present on every field in Base and should contain the user-friendly description that will appear in docstrings.
- When overriding fields in Create/Update requests, use type comments to suppress override warnings:  # type: ignore[override]
  Example:
    user_id: Optional[UUID] = Field(  # type: ignore[override]
        nullable=False, description="ID of the user who owns this product."
    )

Pagination specifics
- Use PaginatedRequestMixin on Get requests to automatically include page and page_size. The docstring must explicitly mention page and page_size in Attributes.
- Use PaginatedResponseMixin on Get responses and set:
    data: List[<ModelName>Response]
  This ensures FastAPI can validate the response model.

Scaffolding algorithm for agentic runs (how to generate a full schemas.py from a single Base)
1. Locate the first class in file with name ending in "Base" that subclasses SQLModel (e.g., ProductBase, InvoiceBase).
2. Parse all fields from that Base: name, type, default, Field(..., description=...).
3. Create the following classes using templates and the exact descriptions extracted:
   - <ModelName>Response
   - Create<ModelName>Request
   - Create<ModelName>Response
   - Get<ModelName>Request
   - Get<ModelName>Response
   - Update<ModelName>Request
   - Update<ModelName>Response
   - Delete<ModelName>Request
   - Delete<ModelName>Response
4. For any "<Base>Item" or child Base classes (e.g., InvoiceItemBase) repeat steps 1–3 to scaffold their corresponding set of I/O classes.
5. For each created class, generate docstrings by copying the Attributes block directly from the Base model and adapting the top-line:
   - "Request model for creating a new <model>." for CreateRequest
   - "Response model for creating a new <model>." for CreateResponse
   - "Request model for retrieving <plural model> with filtering and pagination." for GetRequest
   - "Response model for retrieving <plural model>." for GetResponse
   - "Request model for updating an existing <model>." for UpdateRequest
   - "Response model for updating an existing <model>." for UpdateResponse
   - "Response model for deleting a <model>." for DeleteResponse
6. For UpdateRequest, create Optional overrides for every Base field except id and timestamps. Use default=None and include the exact description.
7. For CreateRequest override any owner/user_id fields to Optional if the project convention allows (use # type: ignore[override]).
8. Add required imports (typing, uuid, Field, SQLModel, mixins). Add datetime import if any Base field type is datetime.
9. Ensure GetResponse.data uses the concrete Response model type in a List[] annotation.

Templates (exact canonical snippets)
- Response class:
  class <ModelName>Response(<ModelName>Base, IDMixin, TimestampMixin):
      """
      Response model for a <model>.

      Attributes:
          <copy Base Attributes verbatim>
          created_at (datetime): Timestamp when the record was created.
          updated_at (datetime): Timestamp when the record was last updated.
      """
      pass

- CreateRequest override for owner id:
  class Create<ModelName>Request(<ModelName>Base):
      """
      Request model for creating a new <model>.

      Attributes:
          <copy Base Attributes verbatim, user_id typed as Optional[UUID]>
      """
      user_id: Optional[UUID] = Field(  # type: ignore[override]
          nullable=False, description="<exact description from Base Field>"
      )

- GetRequest and GetResponse:
  class Get<ModelName>Request(<ModelName>Base, OptionalIDMixin, PaginatedRequestMixin):
      """
      Request model for retrieving <plural model> with filtering and pagination.

      Attributes:
          id (Optional[UUID]): Unique identifier for the record.  # if OptionalIDMixin used
          <copy Base Attributes verbatim>
          page (int): Page number for pagination.
          page_size (int): Number of records per page for pagination.
      """
      pass

  class Get<ModelName>Response(PaginatedResponseMixin):
      """
      Response model for retrieving <plural model>.

      Attributes:
          data (list[<ModelName>Response]): List of model records.
          total (int): Total number of records available.
          next_page (bool): Indicates if there is a next page.
      """
      data: List[<ModelName>Response]

Edge cases and advanced rules
- If Base class includes foreign_key fields, preserve foreign_key and ondelete in Field() definitions.
- If Base uses special constraints (unique=True, index=True) retain them.
- If a Base field uses Enum types, reference the Enum in the annotation and copy description.
- If a field type is "date" vs "datetime", preserve the exact import and docstring type.
- For boolean flags used by system processes (e.g., fbr_validated), in CreateRequest it is acceptable to provide defaults in Base; do not remove default in CreateRequest unless front-end must override.
- Avoid adding business logic or validators in schema files unless strictly necessary; keep them pure structural models. If validation is required, prefer to add pydantic validators in a separate validation module or in service layer functions.

Why these rules
- The exact docstring and Field description copying enables deterministic parsing by agents: attributes can be extracted and reused to produce API docs, serializers, and test fixtures.
- Strict composition with mixins ensures consistent pagination, timestamps, ID semantics and reduces boilerplate per module.

Example minimal generation flow (what an agent should do)
- Input: src\module\schemas.py containing only ProductBase.
- Steps executed:
  1. Read file, find ProductBase, extract fields/descriptions.
  2. Emit imports and mixins.
  3. Emit ProductResponse, CreateProductRequest, CreateProductResponse.
  4. Emit GetProductRequest/GetProductResponse (with Paginated mixins).
  5. Emit UpdateProductRequest/UpdateProductResponse and DeleteProductResponse.
  6. Save file at same path, preserving existing Base class.

## Service Layer Patterns (service.py)

### Function Signature Pattern
```python
# src\module_name\service.py

from typing import List, cast
from src.auth.models import AuthUser
from src.module_name.schemas import GetModelRequest, GetModelResponse
from src.module_name.models import ModelBase, ModelTable

async def get_models(
    auth_user: AuthUser,
    input_params: GetModelRequest
) -> GetModelResponse:
    """
    Retrieve models with filtering and pagination.
    
    Args:
        auth_user: Authenticated user context with session and user details
        input_params: Request parameters including filters and pagination
        
    Returns:
        GetModelResponse: Paginated list of models
        
    Raises:
        NotFoundException: When no models found
        ForbiddenException: When user lacks permissions
    """
    session = auth_user.session
    user_id = auth_user.user.id
    
    # Build query with filters
    statement = select(ModelTable).where(ModelTable.user_id == user_id)
    
    # Apply pagination
    offset = (input_params.page - 1) * input_params.size
    statement = statement.offset(offset).limit(input_params.size)
    
    # Execute query
    models = session.exec(statement).all()
    
    # Cast ORM objects to schema objects
    models = cast(List[ModelBase], models)
    
    return GetModelResponse(
        data=models, 
        total=len(models), 
        page=input_params.page, 
        size=input_params.size
    )
```

### Critical Service Layer Rules

#### Object Casting Pattern
Always cast ORM objects to schema objects for responses:
```python
# Preferred method - efficient casting
models = session.exec(statement).all()
models = cast(List[ModelBase], models)

# Alternative methods (use when casting not possible)
# Method 1: Manual instantiation
models_base = [
    ModelBase(id=model.id, name=model.name, ...) 
    for model in models
]

# Method 2: Model validation
models_base = [
    ModelBase.model_validate(model) 
    for model in models
]
```

#### Function Requirements
- All functions must be `async`
- Accept `auth_user: AuthUser` as first parameter
- Accept request schema as `input_data` (POST/PATCH/PUT/DELETE) or `input_params` (GET)
- Use `auth_user.session` for database operations
- Use `auth_user.user.id` and `auth_user.user.role` for permissions
- Always cast ORM objects to schema objects before returning
- Handle exceptions appropriately

#### Permission Checking Pattern
```python
# Check user permissions
if auth_user.user.role not in ['admin', 'manager']:
    raise ForbiddenException(
        message="Insufficient permissions", 
        detail="User role does not allow this operation"
    )

# Filter by user ownership
statement = select(ModelTable).where(ModelTable.user_id == auth_user.user.id)
```

## Router Patterns (router.py)

### Endpoint Structure
```python
# src\module_name\router.py

from fastapi import APIRouter, Query
from src.dependencies import AuthenticatedUser
from src.auth.models import AuthUser
from src.exceptions import HTTPException, InternalServerErrorException
from src.module_name.schemas import GetModelRequest, GetModelResponse
from src.module_name.service import get_models

router = APIRouter()

@router.get("/", response_model=GetModelResponse)
async def get_models_endpoint(
    auth_user: AuthUser = AuthenticatedUser,
    input_params: GetModelRequest = Query()
) -> GetModelResponse:
    """
    Retrieve models with filtering and pagination.
    
    Returns:
        GetModelResponse: Paginated list of models with metadata
        
    Raises:
        HTTPException: For client errors (400, 404, 403)
        InternalServerErrorException: For server errors (500)
    """
    try:
        return await get_models(auth_user, input_params)
    
    except HTTPException as e:
        raise e
        
    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to retrieve models",
            detail=str(e),
            extra={"operation": "get_models", "user_id": auth_user.user.id}
        )

@router.post("/", response_model=CreateModelResponse)
async def create_model_endpoint(
    input_data: CreateModelRequest,
    auth_user: AuthUser = AuthenticatedUser
) -> CreateModelResponse:
    """
    Create a new model instance.
    
    Args:
        input_data: Model creation data
        auth_user: Authenticated user context
        
    Returns:
        CreateModelResponse: Created model details
    """
    try:
        return await create_model(auth_user, input_data)
    
    except HTTPException as e:
        raise e
        
    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to create model",
            detail=str(e),
            extra={"operation": "create_model", "user_id": auth_user.user.id}
        )
```

### Router Requirements
- All endpoints are `async`
- All routes are protected by default using `AuthenticatedUser` dependency
- Use empty base path (prefix added in main.py)
- Handle `HTTPException` by re-raising
- Catch all other exceptions and raise `InternalServerErrorException`
- Use descriptive error messages with `detail` and `extra` fields
- Import exceptions from `src.exceptions`

### HTTP Method Mapping
- `GET /` - List/retrieve with pagination and filtering
- `GET /{id}` - Get single item by ID
- `POST /` - Create new item
- `PATCH /{id}` or `PATCH /` - Update existing item
- `DELETE /{id}` or `DELETE /` - Delete item(s)

## Exception Handling

### Available Exceptions
Use these from `src.exceptions` instead of `fastapi.HTTPException`:
- `BadRequestException` (400)
- `NotFoundException` (404)
- `ForbiddenException` (403)
- `InternalServerErrorException` (500)

### Exception Best Practices
```python
# Good exception with context
raise NotFoundException(
    message="Model not found",
    detail=f"No model found with ID {model_id}",
    extra={"model_id": model_id, "user_id": auth_user.user.id}
)

# Service layer exception handling
try:
    result = await some_operation()
except HTTPException:
    raise  # Re-raise HTTP exceptions
except Exception as e:
    raise InternalServerErrorException(
        message="Operation failed",
        detail=str(e),
        extra={"context": "additional_info"}
    )
```

## Database Patterns

### Query Building
```python
from sqlmodel import select, col

# Basic query
statement = select(ModelTable)

# With filters
statement = statement.where(ModelTable.user_id == user_id)

# With multiple conditions
statement = statement.where(
    ModelTable.user_id == user_id,
    ModelTable.status == 'active'
)

# Using col() for IN operations
statement = statement.where(col(ModelTable.id).in_(id_list))

# Pagination
offset = (page - 1) * page_size
statement = statement.offset(offset).limit(page_size)
```

### Session Operations
```python
# Query execution
result = session.exec(statement)
models = result.all()  # or .first() for single result

# Create
model = ModelTable(**data)
session.add(model)
await session.commit()
await session.refresh(model)

# Update
model.field = new_value
session.add(model)
await session.commit()
await session.refresh(model)

# Delete
await session.delete(model)
await session.commit()
```

## Quick Setup Checklist

For any new module, create these files following the patterns:

1. **schemas.py**: Define request/response schemas
2. **service.py**: Implement business logic functions
3. **router.py**: Create FastAPI endpoints
4. **Import in main.py**: Add router to main application

### Template Commands
Use these patterns to quickly scaffold:

1. Create schemas with proper inheritance
2. Implement service functions with casting
3. Set up router endpoints with error handling
4. Test with proper authentication

Remember: Always follow the established patterns for consistency and maintainability across the codebase.