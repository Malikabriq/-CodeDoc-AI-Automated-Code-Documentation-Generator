# 📄 `app/models.py` – Developer Documentation

---

## 1. Module Purpose

**What this file is responsible for**

- Defines the **domain data models** used throughout the application for representing a *task* and the payload required to update a task.
- Provides **validation**, **type‑safety**, and **derived/computed properties** (e.g., progress percentage) via **Pydantic**.

**Why it exists in the project**

- Centralises the schema of core business objects so that all layers (API, service, persistence) work against a single source‑of‑truth.
- Leverages Pydantic’s declarative field definitions to enforce constraints (e.g., allowed enum values, numeric bounds) automatically at runtime, reducing boiler‑plate validation code elsewhere.

---

## 2. Key Components

### `Task` (inherits `pydantic.BaseModel`)

| Aspect | Description |
|--------|-------------|
| **Purpose** | Immutable representation of a single work item. |
| **Fields** | <ul><li>`id: str` – Unique identifier (required). Example: `"T001"`.</li><li>`title: str` – Short title (required).</li><li>`description: str` – Full description (required).</li><li>`priority: Literal['low', 'medium', 'high']` – Business‑defined priority (required).</li><li>`status: Literal['pending', 'in_progress', 'completed']` – Current lifecycle state (required).</li><li>`estimated_hours: float` – Expected effort; must be **> 0** (required).</li><li>`hours_spent: float` – Accumulated effort; must be **≥ 0** (required).</li></ul> |
| **Computed fields** | <ul><li>`progress: float` – Read‑only property returning the completion percentage (rounded to 2 decimals). Calculated as <code>(hours_spent / estimated_hours) * 100</code>. Returns `0.0` when `estimated_hours` is falsy.</li><li>`verdict: str` – Human‑readable status derived from `progress`.<br>  • `100` → `"Task Completed"`<br>  • `≥ 70` → `"Almost Done"`<br>  • `≥ 30` → `"In Progress"`<br>  • otherwise → `"Just Started"`</li></ul> |
| **Public API** | The class itself (`Task`) and its two computed properties (`progress`, `verdict`). Instances are serialisable to JSON via `model.json()` or `model.dict()` (default Pydantic behaviour). |
| **Internal Logic Overview** | - Pydantic validates field types and constraints on instantiation.<br>- `@computed_field` + `@property` registers the two read‑only attributes as *virtual fields* that are included in model serialization (`dict()`, `json()`).<br>- The `progress` calculation guards against division by zero. |
| **Typical Usage** | Creating a new task record, passing it through API responses, or persisting it after validation. |

---

### `TaskUpdate` (inherits `pydantic.BaseModel`)

| Aspect | Description |
|--------|-------------|
| **Purpose** | Schema for *partial* updates of an existing `Task`. All fields are optional to allow PATCH‑style updates. |
| **Fields** | <ul><li>`title: Optional[str]` – New title, if supplied.</li><li>`description: Optional[str]` – New description, if supplied.</li><li>`priority: Optional[Literal['low', 'medium', 'high']]` – New priority.</li><li>`status: Optional[Literal['pending', 'in_progress', 'completed']]` – New status.</li><li>`estimated_hours: Optional[float]` – New estimate; must be **> 0** when provided.</li><li>`hours_spent: Optional[float]` – New spent hours; must be **≥ 0** when provided.</li></ul> |
| **Public API** | The class itself (`TaskUpdate`). Consumers typically instantiate it from request payloads and then merge the provided fields into an existing `Task` instance. |
| **Internal Logic Overview** | - Because all attributes default to `None`, Pydantic only validates a field when it is present in the input data.<br>- Numeric constraints (`gt=0`, `ge=0`) are applied only when the corresponding field is supplied. |
| **Typical Usage** | Receiving a JSON body of a PATCH request, validating it, and applying the changes to a stored `Task`. |

---

## 3. Dependencies & Relationships

### Imports

| Import | Origin | Reason for Use |
|--------|--------|----------------|
| `BaseModel`, `Field`, `computed_field` | `pydantic` | Core model base class, field metadata, and declaration of computed properties that behave like regular fields during serialization. |
| `Annotated` | `typing` (Python 3.9+) | Allows attaching Pydantic `Field` metadata directly to type hints. |
| `Literal` | `typing` | Restricts string fields to a finite set of allowed values (enums without an explicit `Enum` class). |
| `Optional` | `typing` | Marks fields as nullable/absent for the update schema. |

### Interaction with Other Project Modules (logical inference)

| Direction | Component | Rationale |
|-----------|-----------|-----------|
| **Depends on** | Any API layer (e.g., FastAPI routers) that declares request/response bodies using `Task` or `TaskUpdate`. | The models provide the schema for request validation and response generation. |
| **Depends on** | Persistence layer (e.g., repository or ORM) that stores `Task` objects. | `Task` instances are likely converted to/from database rows. |
| **Potential Dependents** | Business‑logic services that compute additional metrics or orchestrate workflow steps using `Task.progress` or `Task.verdict`. | Computed fields give services ready‑made insight without re‑implementing the calculation. |
| **Potential Dependents** | Unit‑test suite that creates `Task`/`TaskUpdate` fixtures for testing endpoints or services. | Direct model construction is the simplest way to generate test data. |

### Architectural Fit

- **Domain Layer**: `models.py` sits in the domain (or “core”) package, encapsulating the essential business entities.
- **Transport Layer**: API routers import the models to declare request bodies (`TaskUpdate`) and response models (`Task`).
- **Persistence Layer**: A repository or data‑access object translates between `Task` and the storage format (e.g., a SQL row or a NoSQL document). Since `Task` is a pure Pydantic model, it remains storage‑agnostic.
- **Service Layer**: Business functions receive `Task` instances, may mutate them (by constructing a new model with updated fields) and return the updated object.

---

## 4. Workflow Description

1. **Model Instantiation (Task)**  
   - Input data (e.g., JSON payload) is parsed by Pydantic.  
   - Pydantic validates each field against its type and constraints (`gt`, `ge`, `Literal`).  
   - Upon success, a `Task` instance is created with the raw data.

2. **Computed Field Evaluation**  
   - When `task.progress` or `task.verdict` is accessed, the associated `@property` runs.  
   - `progress` computes `(hours_spent / estimated_hours) * 100` → rounded to two decimals, guarding against division‑by‑zero.  
   - `verdict` selects a textual label based on the numeric `progress`.

3. **Serialization**  
   - Calls like `task.dict()` or `task.json()` include the computed fields automatically because of `@computed_field`.  
   - This enables API responses to expose `progress` and `verdict` without extra code.

4. **Partial Update Flow (TaskUpdate)**  
   - A PATCH request body is parsed into a `TaskUpdate` instance.  
   - Pydantic validates only the supplied keys.  
   - Application logic iterates over the fields of `TaskUpdate`; any non‑`None` value replaces the corresponding attribute on the stored `Task` (often via `task.copy(update={...})`).  
   - After updating numeric fields, `progress` and `verdict` reflect the new state automatically.

5. **Persistence**  
   - The (potentially) updated `Task` instance is handed to the repository layer to be persisted (e.g., `repo.save(task)`).  
   - The repository may convert the model to a dict (`task.dict(exclude_unset=True)`) suitable for the underlying storage engine.

---

## 5. Usage Examples

> **Note** – The examples assume a typical FastAPI or similar framework context, but they are valid plain‑Python usage as well.

### 5.1 Creating a New Task

```python
from app.models import Task

new_task = Task(
    id="T001",
    title="Write documentation",
    description="Produce developer docs for the models module",
    priority="high",
    status="pending",
    estimated_hours=8.0,
    hours_spent=0.0,
)

print(new_task.progress)   # → 0.0
print(new_task.verdict)    # → "Just Started"
print(new_task.json())     # JSON includes progress & verdict
```

### 5.2 Updating a Task with a Patch Payload

```python
from app.models import Task, TaskUpdate

# Existing task (could come from DB)
task = Task(
    id="T001",
    title="Write documentation",
    description="...",
    priority="high",
    status="in_progress",
    estimated_hours=8.0,
    hours_spent=3.0,
)

# Simulated incoming PATCH payload
payload = {"hours_spent": 6.5, "status": "in_progress"}

update = TaskUpdate(**payload)

# Merge changes – immutable pattern (creates a new instance)
updated_task = task.copy(update=update.dict(exclude_unset=True))

print(updated_task.progress)   # → 81.25
print(updated_task.verdict)    # → "Almost Done"
```

### 5.3 Serializing for an API Response

```python
# FastAPI endpoint example
from fastapi import APIRouter, HTTPException
from app.models import Task, TaskUpdate

router = APIRouter()

@router.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: str):
    task = repository.get(task_id)          # fetch from DB
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task                              # FastAPI uses .dict() under the hood
```

---

## 6. Notes for Developers

| Area | Guidance / Pitfalls |
|------|----------------------|
| **Immutability** | `Task` is a subclass of `BaseModel` with default *mutable* behaviour. If you need strict immutability, consider `Config.frozen = True`. Current code relies on the **copy‑update** pattern (`task.copy(update=…)`) for safe modifications. |
| **Computed Field Inclusion** | `@computed_field` ensures `progress` and `verdict` appear in `dict()`/`json()`. Forgetting the decorator will hide them from API responses. |
| **Division by Zero** | The `progress` property guards against a zero `estimated_hours`. If a task legitimately has `estimated_hours == 0`, `progress` will always be `0.0`. Validate upstream that such a state is intentional. |
| **Enum Alternatives** | Using `Literal` provides compile‑time clarity but lacks runtime introspection utilities (e.g., listing allowed values). If you need richer enum features (methods, auto‑documentation), replace `Literal` with `Enum`. |
| **Field Validation** | The `gt`/`ge` constraints are enforced **only when a value is provided**. In `TaskUpdate`, a `None` value bypasses validation, which is appropriate for partial updates. |
| **Serialization Options** | When persisting to a DB, you may want to exclude computed fields (`exclude={'progress', 'verdict'}`) because they can be derived later. |
| **Version Compatibility** | This file uses `typing.Annotated` (Python 3.9+). Ensure the runtime environment meets this requirement, or replace with the older `Field` syntax if needed. |
| **Testing** | Unit tests should cover: <ul><li>Invalid enum values raise `ValidationError`.</li><li>Numeric constraints (`gt`, `ge`).</li><li>Correct computation of `progress` and `verdict` for edge cases (0 %, 30 %, 70 %, 100 %).</li></ul> |
| **Extensibility** | If additional derived metrics are required (e.g., `remaining_hours`), implement them as additional `@computed_field` properties to keep the API surface consistent. |

--- 

*End of documentation for `app/models.py`.*