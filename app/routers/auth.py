from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import (
    UserRegister, UserLogin, Token, OTPVerify, 
    ForgotPassword, ResetPassword, GoogleAuth, UserOut, OTPResend
)
from app.crud import auth as crud_auth
from app.core.security import verify_password, create_access_token
from app.services.email_service import send_otp_email

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    # 1. Cek apakah email sudah terdaftar
    existing_user = await crud_auth.get_user_by_email(db, data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email sudah terdaftar."
        )
    
    # 2. Validasi password
    if data.password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password dan konfirmasi password tidak cocok."
        )
    
    # 3. Create user
    user = await crud_auth.create_user(
        db, full_name=data.full_name, email=data.email, password=data.password
    )
    
    # 4. Generate & Send OTP
    otp = await crud_auth.update_user_otp(db, user)
    await send_otp_email(user.email, otp)
    
    return user


@router.post("/verify-otp")
async def verify_otp(data: OTPVerify, db: AsyncSession = Depends(get_db)):
    user = await crud_auth.get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan.")
    
    if user.otp_code != data.otp_code:
        raise HTTPException(status_code=400, detail="Kode OTP salah.")
    
    if user.otp_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Kode OTP sudah kadaluarsa.")
    
    user.is_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    await db.commit()
    
    return {"message": "Email berhasil diverifikasi."}


@router.post("/resend-otp")
async def resend_otp(data: OTPResend, db: AsyncSession = Depends(get_db)):
    user = await crud_auth.get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan.")
    
    otp = await crud_auth.update_user_otp(db, user)
    await send_otp_email(user.email, otp)
    
    return {"message": "OTP baru telah dikirim ke email."}


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await crud_auth.get_user_by_email(db, data.email)
    if not user or not user.hashed_password:
        raise HTTPException(status_code=400, detail="Email atau password salah.")
    
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Email atau password salah.")
    
    if not user.is_verified:
        raise HTTPException(status_code=401, detail="Email belum diverifikasi.")
    
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/forgot-password")
async def forgot_password(data: ForgotPassword, db: AsyncSession = Depends(get_db)):
    user = await crud_auth.get_user_by_email(db, data.email)
    if user:
        otp = await crud_auth.update_user_otp(db, user)
        await send_otp_email(user.email, otp)
    
    # Selalu return success demi keamanan (agar tidak bisa menebak email terdaftar)
    return {"message": "Instruksi reset password telah dikirim ke email jika akun terdaftar."}


@router.post("/reset-password")
async def reset_password(data: ResetPassword, db: AsyncSession = Depends(get_db)):
    user = await crud_auth.get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan.")
    
    if user.otp_code != data.otp_code:
        raise HTTPException(status_code=400, detail="Kode OTP salah.")
    
    if user.otp_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Kode OTP sudah kadaluarsa.")
    
    from app.core.security import get_password_hash
    user.hashed_password = get_password_hash(data.new_password)
    user.otp_code = None
    user.otp_expires_at = None
    await db.commit()
    
    return {"message": "Password berhasil diperbarui."}


@router.post("/google", response_model=Token)
async def google_auth(data: GoogleAuth, db: AsyncSession = Depends(get_db)):
    """
    Endpoint untuk login/register via Google.
    Aplikasi mobile akan mengirimkan id_token dari Google.
    """
    # NOTE: Di sini harus ada verifikasi id_token menggunakan library google-auth
    # Untuk demo, kita asumsikan verifikasi berhasil dan mendapatkan data profil
    # placeholder_email = "user@gmail.com"
    # placeholder_name = "Google User"
    # placeholder_google_id = "123456789"
    
    raise HTTPException(
        status_code=501, 
        detail="Google Auth verification logic needs to be implemented with google-auth library."
    )
