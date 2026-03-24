# Test

# Employee Management Endpoints

This document lists all current web and API endpoints, what they do, auth requirements, and payload formats.

Base URL (local): ⁠ http://127.0.0.1:8000 ⁠

---

## 1) Authentication

### 1.1 Web session auth (⁠ /accounts/ ⁠)

•⁠  ⁠⁠ GET /accounts/login/ ⁠ - login page (Django session login)
•⁠  ⁠⁠ POST /accounts/login/ ⁠ - submit login form
•⁠  ⁠⁠ POST /accounts/logout/ ⁠ - logout current session

Used by browser-based web views protected with ⁠ @login_required ⁠.

### 1.2 JWT auth API (⁠ /api/accounts/ ⁠)

#### ⁠ POST /api/accounts/login/ ⁠
Get JWT access + refresh tokens.

Request:
⁠ json
{
  "username": "admin",
  "password": "admin123"
}
 ⁠

Response:
⁠ json
{
  "refresh": "<refresh_token>",
  "access": "<access_token>"
}
 ⁠

#### ⁠ POST /api/accounts/refresh/ ⁠
Refresh access token.

Request:
⁠ json
{
  "refresh": "<refresh_token>"
}
 ⁠

---

## 2) Dynamic Forms

### 2.1 Web builder (⁠ /forms/ ⁠)

#### ⁠ GET /forms/get-form/ ⁠
Open dynamic form builder UI.
Authentication: *Required* (session login)

#### ⁠ POST /forms/get-form/ ⁠
Create dynamic form from web AJAX payload.
Authentication: *Required* (session login + CSRF)

### 2.2 Forms API (⁠ /api/forms/ ⁠)

#### ⁠ POST /api/forms/create/ ⁠
Create a dynamic form and fields.
Authentication: *Required* (⁠ IsAuthenticated ⁠)

Request:
⁠ json
{
  "form_name": "Employee Intake",
  "fields": [
    { "label": "joining date", "field_type": "date", "required": true },
    { "label": "name", "field_type": "text", "required": true },
    { "label": "salary", "field_type": "number", "required": false }
  ]
}
 ⁠

Success response (⁠ 201 ⁠):
⁠ json
{
  "success": true,
  "id": 1
}
 ⁠

Rules:
•⁠  ⁠Allowed ⁠ field_type ⁠: ⁠ text ⁠, ⁠ number ⁠, ⁠ date ⁠, ⁠ password ⁠
•⁠  ⁠Field labels are normalized (trim + collapse spaces + lowercase)
•⁠  ⁠Duplicate labels in same form are rejected (case-insensitive)

---

## 3) Employee Web Endpoints (⁠ /employee/ ⁠)

#### ⁠ GET /employee/create/ ⁠
Open employee create page.
Authentication: *Not required*

#### ⁠ GET /employee/list/ ⁠
Show employee list page.
Authentication: *Required*

Optional query params:
•⁠  ⁠⁠ field_label ⁠
•⁠  ⁠⁠ field_value ⁠

Example:
⁠ /employee/list/?field_label=name&field_value=sure ⁠

#### ⁠ GET /employee/forms/<form_id>/fields/ ⁠
Fetch fields for selected dynamic form.
Authentication: *Required*

#### ⁠ POST /employee/submit/ ⁠
Create user + employee from web payload.
Authentication: *Required* (session + CSRF)

Request:
⁠ json
{
  "username": "suren",
  "email": "suren@example.com",
  "first_name": "Suren",
  "last_name": "K",
  "password": "StrongPass123!",
  "form_id": 1,
  "answers": {
    "joining date": "2026-03-24",
    "name": "Suren K"
  }
}
 ⁠

#### ⁠ POST /employee/<pk>/delete/ ⁠
Soft-delete one employee record.
Authentication: *Required* (session + CSRF)

Behavior:
•⁠  ⁠sets ⁠ is_deleted = true ⁠
•⁠  ⁠sets ⁠ deleted_at ⁠
•⁠  ⁠does *not* delete the related ⁠ User ⁠

---

## 4) Employee API CRUD (⁠ /api/employee/ ⁠)

### ⁠ GET /api/employee/employees/ ⁠
Paginated employee list (non-deleted records only).
Authentication: currently *not required* (⁠ AllowAny ⁠ in view)

Pagination query params:
•⁠  ⁠⁠ page ⁠ (default 1)
•⁠  ⁠⁠ page_size ⁠ (default 10, max 100)

Sorting query params:
•⁠  ⁠⁠ sort_by ⁠: ⁠ id ⁠, ⁠ created_at ⁠, ⁠ updated_at ⁠, ⁠ username ⁠, ⁠ form_name ⁠
•⁠  ⁠⁠ order ⁠: ⁠ asc ⁠ or ⁠ desc ⁠ (default ⁠ desc ⁠)

Example:
⁠ /api/employee/employees/?page=1&page_size=20&sort_by=username&order=asc ⁠

### ⁠ POST /api/employee/employees/ ⁠
Create employee + linked user + dynamic ⁠ form_data ⁠.
Authentication: currently *not required* (⁠ AllowAny ⁠)

Request:
⁠ json
{
  "username": "jdoe",
  "email": "jane@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "password": "StrongPass123!",
  "form_id": 1,
  "answers": {
    "joining date": "2026-03-24",
    "name": "Jane Doe"
  }
}
 ⁠

### ⁠ GET /api/employee/employees/<pk>/ ⁠
Retrieve one employee by id.

### ⁠ PUT /api/employee/employees/<pk>/ ⁠
Full update.

### ⁠ PATCH /api/employee/employees/<pk>/ ⁠
Partial update.

Updatable keys:
•⁠  ⁠⁠ username ⁠
•⁠  ⁠⁠ email ⁠
•⁠  ⁠⁠ first_name ⁠
•⁠  ⁠⁠ last_name ⁠
•⁠  ⁠⁠ password ⁠
•⁠  ⁠⁠ form_id ⁠
•⁠  ⁠⁠ answers ⁠

Notes:
•⁠  ⁠If ⁠ form_id ⁠ changes, include ⁠ answers ⁠ for that new form
•⁠  ⁠⁠ answers ⁠ are validated against selected form's dynamic field definitions

### ⁠ DELETE /api/employee/employees/<pk>/ ⁠
Soft-delete one employee record.
Behavior:
•⁠  ⁠marks employee deleted (⁠ is_deleted ⁠, ⁠ deleted_at ⁠)
•⁠  ⁠related ⁠ User ⁠ is retained

---

## 5) Validation Summary

•⁠  ⁠Dynamic form answers:
  - ⁠ number ⁠ must be numeric
  - ⁠ date ⁠ must be ⁠ YYYY-MM-DD ⁠
  - required fields must be present
•⁠  ⁠User uniqueness:
  - username must be unique
  - email must be unique (if provided)
•⁠  ⁠Password policy:
  - Django password validators are applied (minimum length, common password checks, etc.)
