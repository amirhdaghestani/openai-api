from fastapi import HTTPException

limit_exception = HTTPException(
    status_code=429, detail="Limit has been surpassed. Contact adminstration.")

forbidden_exception = HTTPException(
    status_code=403,
    detail="You do not have the privilage to access this endpoint. " \
           "Contact administration."
)

owner_removal_exception = HTTPException(
    status_code=403,
    detail="Owner cannot be removed."
)

self_removal_exception = HTTPException(
    status_code=403,
    detail="Self User cannot be removed."
)

admin_remove_admin_exception = HTTPException(
    status_code=403,
    detail="Admin cannot remove another user with Admin privilege."
)

admin_add_owner_exception = HTTPException(
    status_code=403,
    detail="Admin cannot add user with Owner privilege."
)

admin_add_admin_exception = HTTPException(
    status_code=403,
    detail="Admin cannot add user with Admin privilege."
)

admin_update_owner_exception = HTTPException(
    status_code=403,
    detail="Admin cannot update user with Owner privilege."
)

admin_update_admin_exception = HTTPException(
    status_code=403,
    detail="Admin cannot update user with Admin privilege."
)

wrong_password_exception = HTTPException(
    status_code=401,
    detail="Incorrect username or password")
