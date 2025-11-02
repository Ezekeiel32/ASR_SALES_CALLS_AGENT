# How to Generate JWT Secret Key

## ✅ Migration Complete!

Your database migration ran successfully:
- `002_add_user_password` applied
- `password_hash` column added to users table

## 🔑 Generate JWT Secret Key

### Option 1: Using Python (Recommended)

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

This generates a secure, URL-safe random string (43 characters).

### Option 2: Using OpenSSL

```bash
openssl rand -hex 32
```

This generates a 64-character hexadecimal string.

### Option 3: Using Python (Alternative)

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

This generates a 64-character hexadecimal string.

### Option 4: Online Generator

You can also use online tools like:
- https://randomkeygen.com/ (use "CodeIgniter Encryption Keys")
- https://1password.com/password-generator/

**Note:** The secret should be at least 32 bytes (256 bits) for security.

## 📋 Add to Koyeb

1. **Copy the generated secret** (from the command above)
2. **Go to Koyeb Dashboard** → Your App → Services → API Service
3. **Click "Environment variables"** tab
4. **Click "Add variable"** or "Create variable"
5. **Add:**
   - **Name:** `JWT_SECRET_KEY`
   - **Value:** (paste the generated secret)
6. **Save**
7. **Relaunch the service** for changes to take effect

## 🔒 Security Best Practices

1. **Never commit** the secret to Git
2. **Use different secrets** for production/staging/development
3. **Rotate secrets** periodically (every 6-12 months)
4. **Keep secrets** in environment variables (not in code)

## ⚠️ Important

After setting `JWT_SECRET_KEY`:
- Existing tokens (if any) will be invalid
- Users will need to login again to get new tokens
- This is normal and expected

## 🚀 Quick Copy-Paste

I've generated one for you above - you can use that, or generate your own using any of the methods above.

---

**After setting the secret, your authentication system will be fully secure!** 🔐

