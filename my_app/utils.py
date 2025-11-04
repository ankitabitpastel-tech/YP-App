import hashlib

def encrypt_id(user_id):
    md5_hash = hashlib.md5(str(user_id).encode()).hexdigest()
    print(f"DEBUG encrypt_id: {md5_hash}")

    return md5_hash
def encrypt_id(company_id):
    md5_hash = hashlib.md5(str(company_id).encode()).hexdigest()
    print(f"DEBUG encrypt_id: {md5_hash}")

    return md5_hash

def get_user_by_encrypted_id(encrypted_id):
    from .models import user
    try:
        users = user.objects.all()
        for u in users:
            if encrypt_id(u.id) == encrypted_id:
                return u
    except Exception as e:
        print(f"Error in get_user_by_encrypted_id: {e}")
        return None

    return None

def get_company_by_encrypted_id(encrypted_id):
    from .models import company
    companies = company.objects.all()
    for company in companies:
        if encrypt_id(company.id) == encrypted_id:
            return company
    return None
