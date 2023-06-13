from fastapi import HTTPException

limit_exception = HTTPException(
    status_code=429, detail="Limit has been surpassed. Contact adminstration.")

forbidden_exception = HTTPException(
    status_code=403,
    detail="You do not have the privilage to access this endpoint. " \
           "Contact administration."
)
