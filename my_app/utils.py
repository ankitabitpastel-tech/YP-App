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


def get_company_follower_by_encrypted_id(encrypted_id):
    from .models import company_followers
    all_followers = company_followers.objects.all()
    for follower in all_followers:
        if encrypt_id(follower.id) == encrypted_id:
            return follower
    return None

def get_job_post_by_encrypted_id(encrypted_id):
    from .models import job_posts
    try:
        all_job_posts = job_posts.objects.all()
        for job_post in all_job_posts:
            if encrypt_id(job_post.id) == encrypted_id:
                return job_post
        return None
    except Exception as e:
        print(f"Error in get_job_post_by_encrypted_id: {str(e)}")
        return None
