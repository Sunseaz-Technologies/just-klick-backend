from ninja import Schema
from pydantic import BaseModel
from typing import List


class GoogleAuthIn(BaseModel):
    id_token: str
    


class AuthTokenOut(BaseModel):
    success: bool
    status: str | None = None
    access: str | None = None
    refresh: str | None = None
    message: str | None = None
    onboarding_complete: bool | None = None


class SendOTPIn(Schema):
    phone: str
    email: str | None = None


class VerifyOTPIn(Schema):
    phone: str
    otp: str


class ResendOTPIn(Schema):
    phone: str
    purpose: str = "REGISTER"


class MessageOut(Schema):
    success: bool
    message: str


class StudentRegisterIn(Schema):
    first_name: str
    last_name: str
    email: str
    phone: str
    otp: str


class StudentLoginIn(Schema):
    phone: str | None = None
    email: str | None = None
    otp: str


class TokenRefreshIn(Schema):
    refresh_token: str


class StudentOnboardingSchema(Schema):
    father_name: str
    college_code: str
    course: str
    academic_year: str
    year_of_study: str
    cgpa_percentage: str
    course_reason: List[str]
    area_of_interest: List[str]
    skills_to_develop: List[str]
    plan_after_graduation: str
    interested_abroad: bool
    preferred_country: str = ""
    career_goal: str
    internship_completed: bool
    interested_in_internship: bool
    certifications: bool


class StudentProfileUpdateSchema(Schema):
    father_name: str
    college_code: str
    dept_course: str
    academic_year: str
    year_of_study: str
    cgpa_percentage: str
    course_reason: List[str]
    area_of_interest: List[str]
    skills_to_develop: List[str]
    plan_after_graduation: str
    interested_abroad: str
    preferred_country: str = ""
    career_goal: str
    internship_completed: bool
    interested_in_internship: bool
    certifications: bool


class LogoutSchema(Schema):
    refresh_token: str


class LeadSchema(BaseModel):
    business_id: int
    name: str
    email: str
    phone: str
    subject: str
    message: str


class EmailOtpSchema(Schema):
    email: str