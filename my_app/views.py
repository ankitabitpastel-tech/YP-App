from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .models import user, company, company_followers, job_posts
from django.views.decorators.csrf import csrf_protect
from .utils import encrypt_id, get_user_by_encrypted_id, get_company_by_encrypted_id, get_company_follower_by_encrypted_id, get_job_post_by_encrypted_id
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
import traceback
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.core.validators import validate_email, URLValidator
import re


@csrf_protect
def welcome (request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_obj = authenticate(request, email=email, password=password)

        try: 
            user_obj = user.objects.get(email=email, role='0', status='1')
            if user_obj.check_password(password):
                request.session['user_id']=user_obj.id
                request.session['user_email']=user_obj.email
                request.session['user_name']=user_obj.full_name
                request.session['is_authenticated']=True

                messages.success(request, f'welcome back, {user_obj.full_name}!')

                return redirect('dashboard')
            else:
                messages.error(request, 'Access denied. Only a superuser can login here.')
       
        except Exception as e:
            messages.error(request, f'Login error: {str(e)}')
        except Exception as e:
            messages.error(request, f'Login error: {str(e)}')

    return render (request, 'welcome.html')
   

def super_admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_authenticated'):
            messages.error(request, 'please login first.')
            return redirect('welcome')
        
        user_id = request.session.get('user_id')
        try:
            user_id = user.objects.get(id=user_id, status = '1')
            if user_id.role != '0':
                messages.error(request, 'Access denied. super admin required.')
                return redirect('welcome')
        except user.DoesNotExist:
            messages.error(request, 'User not found') 
            return redirect('welcome')
        
        return view_func(request, *args, **kwargs)
    return wrapper



@super_admin_required
def dashboard(request):
    user_id = request.session.get('user_id')
    user_obj = user.objects.get(id=user_id)

    total_users= user.objects.exclude(status='5').count()
    total_companies= company.objects.exclude(status='5').count()
    total_follows= company_followers.objects.exclude(status='0').count()


    context = {
        'current_user': user_obj,
        'total_users': total_users,
        'total_companies': total_companies,
        'total_follows': total_follows,



    }

    return render(request, 'dashboard.html', context)
    


@super_admin_required
def user_logout(request):
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    return redirect('welcome')

@super_admin_required
def users(request):
    
    # users_list = user.objects.exclude(role='0').exclude(status=5).order_by('-created_at')

    # print(f"Users found: {users_list.count()}")
    # for usr in users_list:
    #     usr.md5_id = encrypt_id(usr.id)

    context = {
        # 'users': users_list,
        'current_user': user.objects.get(id=request.session.get('user_id'))
    }

    return render(request, 'users.html', context)

@super_admin_required
def add_user(request):
    if request.method == 'POST':
        try:
            full_name = request.POST.get('full_name')
            username = request.POST.get('username')
            email = request.POST.get('email')
            phone_no = request.POST.get('phone_no')
            password = request.POST.get('password')
            role = request.POST.get('role')
            status = request.POST.get('status', '1')

            if user.objects.filter(email=email).exists():
                messages.error(request, 'A user with this email already exists.')
                return render(request, 'add_user.html')
            
            new_user = user(
                full_name=full_name,
                username=username if username else None,
                email=email,
                phone_no=phone_no,
                password=password,  
                role=role,
                status=status

            )
            new_user.save()

            messages.success(request, f'user {full_name} added successfully!')
            return redirect('users')
        except Exception as e:
            messages.error(request, f'Error adding member: {str(e)}')
            return render(request, 'add_user.html')
        
    context = {
        'current_user': user.objects.get(id=request.session.get('user_id'))
    }
        
    return render(request, 'add_user.html', context)

@super_admin_required
def edit_user(request, encrypted_id):
    user_obj=get_user_by_encrypted_id(encrypted_id)

    # user_obj=user.objects.get(id=encrypt_id)

    if request.method == 'POST':
        try: 
            full_name = request.POST.get('full_name')
            username = request.POST.get('username')
            email = request.POST.get('email')
            phone_no = request.POST.get('phone_no')
            role = request.POST.get('role')



            user_obj.full_name = full_name
            user_obj.username = username if username else None
            user_obj.email = email
            user_obj.phone_no = phone_no
            user_obj.role = role

            user_obj.updated_at = timezone.now()

            user_obj.save()
            messages.success(request, f'User {full_name} updated successfully!')

            return redirect('users')
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')

        
    context = {
        'current_user': user.objects.get(id=request.session.get('user_id')),
        'user_obj': user_obj
    }
        
    return render(request, 'edit_user.html', context)

@super_admin_required
def delete_user(request, encrypted_id):
    user_obj = get_user_by_encrypted_id(encrypted_id)

    try:
        # user_obj = user.objects.get(id=encrypt_id)
        user_obj.status = '5'
        user_obj.save()
        messages.success(request, f'User {user_obj.full_name} deleted successfully!')
        print(f"{user_obj.full_name} deleted!")
    except user.DoesNotExist:
        messages.error(request, 'User not found!')
    except Exception as e:
        messages.error(request, f'Error deleting user: {str(e)}')
        print(f'Error: {e}')
    
    return redirect('users')

@super_admin_required
def user_details(request, encrypted_id):
    user_obj = get_user_by_encrypted_id(encrypted_id)
    
    if not user_obj:
        messages.error(request, 'User not found!')
        return redirect('users')
    
    user_obj.md5_id = encrypt_id(user_obj.id)
    
    context = {
        'user_obj': user_obj,
        'current_user': user.objects.get(id=request.session.get('user_id'))
    }
    
    return render(request, 'user_details.html', context)


@super_admin_required
def users_data(request):
    try:
        draw = int(request.GET.get('draw', 1))
        start=int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]','')

        queryset = user.objects.exclude(role='0').exclude(status='5')

        if search_value:
            queryset = queryset.filter(
                Q(full_name__icontains=search_value) |
                Q(email__icontains=search_value) |
                Q(username__icontains=search_value) |
                Q(phone_no__icontains=search_value)
            )



        records_total = int(user.objects.exclude(role='0').exclude(status='5').count())

        records_filtered = queryset.count()

        paginator = Paginator(queryset, length)
        page_number = start // length + 1
        page = paginator.get_page(page_number)
        data = []
        for usr in page:
            usr.md5_id = encrypt_id(usr.id)
            data.append({
                "full_name": usr.full_name,
                "username": usr.username,
                "email": usr.email,
                "phone_no": usr.phone_no or "",
                "actions": f"""
                    <div class='btn-group'>
                      <a href='/users/details/{usr.md5_id}/' class='btn btn-sm btn-primary'><i class='fas fa-eye'></i></a>
                      <a href='/users/edit/{usr.md5_id}/' class='btn btn-sm btn-warning'><i class='fas fa-edit'></i></a>
                      <a href='/users/delete/{usr.md5_id}/' class='btn btn-sm btn-danger' onclick="return confirm('Are you sure?')"><i class='fas fa-user-times'></i></a>
                    </div>

                """
            })

        return JsonResponse({
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": data
    })
    except Exception as e:
        return JsonResponse({
            "draw": 1,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)
        })

@super_admin_required
def companies(request):
    company_list = company.objects.exclude(status='5').order_by('created_at')
    for comp in company_list:
        comp.md5_id = encrypt_id(comp.id)

    context = {
        'companies': company_list,
        'current_user': user.objects.get(id=request.session.get('user_id'))
    }
    return render(request, 'companies.html', context)

@super_admin_required
def add_company(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone_no = request.POST.get('phone_no')
            address = request.POST.get('address')
            website = request.POST.get('website')

            errors = {}
            if not email:
                errors['email'] = 'Email is required.'
            else:
                try:
                    validate_email(email)
                except ValidationError:
                    errors['email'] = 'Enter a valid email address.'

                if company.objects.filter(email=email, status__in=['0', '1']).exists():
                    errors['email'] = 'A company with this email already exists.'

            if phone_no:

                phone_digits = re.sub(r'\D', '', phone_no)
                if len(phone_digits) < 10:
                    errors['phone'] = 'Please enter a valid phone number (at least 10 digits).'
                elif len(phone_no) > 20:
                    errors['phone'] = 'Phone number cannot exceed 20 characters.'

            if not name:
                errors['name'] = 'Company name is required.'
            elif len(name) > 255:
                errors['name'] = 'Company name cannot exceed 255 characters.'
            elif company.objects.filter(name=name, status__in=['0', '1']).exists():
                errors['name'] = 'A company with this name already exists.'

            if errors:
                for field, error_message in errors.items():
                    messages.error(request, error_message)
                context = {
                    'current_user': user.objects.get(id=request.session.get('user_id'))
                }
                return render(request, 'add_company.html', context)

            
            new_company = company(
                name=name,
                email=email,
                phone_no=phone_no,
                address=address,
                website=website
            )
            new_company.save()

            messages.success(request, f'Company {name} added successfully!')
            return redirect('companies')
            
        except Exception as e:
            messages.error(request, f'Error adding company: {str(e)}')
            return render(request, 'add_company.html')
    
    context = {
        'current_user': user.objects.get(id=request.session.get('user_id'))
    }
    return render(request, 'add_company.html', context)

@super_admin_required
def edit_company(request, encrypted_id):
    company_obj = get_company_by_encrypted_id(encrypted_id)
    company_obj.md5_id=encrypt_id(company_obj.id)
    if request.method == 'POST':
        try: 
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone_no = request.POST.get('phone_no')
            address = request.POST.get('address')
            website = request.POST.get('website')
            status = request.POST.get('status')

            company_obj.name = name
            company_obj.email = email
            company_obj.phone_no = phone_no
            company_obj.address = address
            company_obj.website = website
            company_obj.status = status
            
            company_obj.updated_at = timezone.now()
            company_obj.save()
            messages.success(request, f'Company {name} updated successfully!')
            return redirect('companies')
            
        except Exception as e:
            messages.error(request, f'Error updating company: {str(e)}')
    
    context = {
        'current_user': user.objects.get(id=request.session.get('user_id')),
        'company_obj': company_obj
    }
    return render(request, 'edit_company.html', context)

@super_admin_required
def company_details(request, encrypted_id):
    company_obj = get_company_by_encrypted_id(encrypted_id)
        
    company_obj.md5_id = encrypt_id(company_obj.id)
    
    context = {
        'company_obj': company_obj,
        'current_user': user.objects.get(id=request.session.get('user_id'))
    }
    return render(request, 'company_details.html', context)

@super_admin_required
def delete_company(request, encrypted_id):
    company_obj = get_company_by_encrypted_id(encrypted_id)
    
    if not company_obj:
        messages.error(request, 'Company not found!')
        return redirect('companies')
    
    try:
        company_obj.status = '5'
        company_obj.save()
        messages.success(request, f'Company {company_obj.name} deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting company: {str(e)}')
    
    return redirect('companies')


@super_admin_required
def companies_data(request):
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        
        queryset = company.objects.exclude(status='5')

        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value) |
                Q(email__icontains=search_value) |
                Q(phone_no__icontains=search_value) |
                Q(address__icontains=search_value) |
                Q(website__icontains=search_value)
            )

        records_total = company.objects.exclude(status='5').count()
        records_filtered = queryset.count()

        paginator = Paginator(queryset, length)
        page_number = start // length + 1
        page = paginator.get_page(page_number)
        
        data = []
        for comp in page:
            comp.md5_id = encrypt_id(comp.id)
            data.append({
                "name": comp.name or "",
                "email": comp.email or "",
                "phone_no": comp.phone_no or "",
                "website": comp.website or "",
                "address": comp.address or "",
                "actions": f"""
                    <div class='btn-group'>
                      <a href='/companies/details/{comp.md5_id}/' class='btn btn-sm btn-primary'><i class='fas fa-eye'></i></a>
                      <a href='/companies/edit/{comp.md5_id}/' class='btn btn-sm btn-warning'><i class='fas fa-edit'></i></a>
                      <a href='/companies/delete/{comp.md5_id}/' class='btn btn-sm btn-danger' onclick="return confirm('Are you sure you want to delete this company?')"><i class='fas fa-building'></i></a>
                    </div>
                """
            })

        response_data = {
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": data
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            "draw": 1,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)
        })

@super_admin_required
def company_followers_list(request):
    context={
        'current_user': user.objects.get(id=request.session.get('user_id'))
    }
    return render(request, 'company_followers_list.html', context)

@super_admin_required
def company_followers_data(request):
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        
        # queryset = company_followers.objects.filter(status='1').select_related('user', 'company')
        queryset = company_followers.objects.exclude(status='0').select_related('user', 'company')


        if search_value:
            queryset = queryset.filter(
                Q(user__full_name__icontains=search_value) |
                Q(user__email__icontains=search_value) |
                Q(company__name__icontains=search_value) |
                Q(company__email__icontains=search_value)

            )
        records_total = company_followers.objects.exclude(status=5).count()
        records_filtered = queryset.count()

        queryset = queryset.order_by('-updated_at')

        paginator = Paginator(queryset, length)
        page_number = start // length + 1
        page = paginator.get_page(page_number)

        data = []
        for follower in page:
            user_md5 = encrypt_id(follower.user.id)
            company_md5 = encrypt_id(follower.company.id)
            # follower_md5 = 

            data.append({
                "user_name": f"<a href='/users/details/{user_md5}/'>{follower.user.full_name}</a>",
                "user_email": follower.user.email,
                "company_name": f"<a href='/companies/details/{company_md5}/'>{follower.company.name}</a>",
                "company_email": follower.company.email,
                "updated_at": follower.updated_at.strftime('%Y-%m-%d %H:%M:%S')if follower.updated_at else "",
                "status": "<span class='badge badge-success'>Following</span>",
                "actions": f"""
                    <div class='btn-group'>
                        <a href='/company_followers/unfollow/{encrypt_id(follower.id)}/' 
                           class='btn btn-sm btn-danger' 
                           onclick="return confirm('Are you sure you want to unfollow?')">
                            <i class='fas fa-user-minus'></i>
                        </a>
                    </div>
                """
            })

        response_data = {
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": data
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            "draw": 1,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)
        })


@super_admin_required
def get_companies_not_followed(request):
    user_id = request.GET.get('user_id')

    if not user_id:
        return JsonResponse({'companies': []})

    try: 
        user_obj = get_user_by_encrypted_id(user_id)
        if not user_obj:
            return JsonResponse({'companies':[]})
        
        all_companies = company.objects.exclude(status='5')

        followed_company_ids = company_followers.objects.filter(
            user=user_obj, 
            status='1'
        ).values_list('company_id', flat=True)

        available_companies = all_companies.exclude(id__in=followed_company_ids)
        
        companies_data = []
        for comp in available_companies:
            companies_data.append({
                'id': encrypt_id(comp.id),
                'name': comp.name,
                'email': comp.email
            })
        
        return JsonResponse({'companies': companies_data})

    except Exception as e:
        return JsonResponse({'companies': [], 'error': str(e)})


@super_admin_required
def add_company_follower(request):
    if request.method == 'POST':
        try:
            user_id = request.POST.get('user_id')
            company_id = request.POST.get('company_id')

            if not user_id or not company_id:
                messages.error(request, 'Both user and company are required.')
                return redirect('add_company_follower')
            user_obj = get_user_by_encrypted_id(user_id)
            company_obj = get_company_by_encrypted_id(company_id)

            if not user_obj or not company_obj:
                messages.error(request, 'Invalid user or company selected.')
                return redirect('add_company_follower')
            
            existing_follower = company_followers.objects.filter(
                user=user_obj,
                company=company_obj
            ).first()
            if existing_follower:
                if existing_follower.status == '1':
                    messages.warning(request, f'{user_obj.full_name} already follows {company_obj.name}' )
                    print(request, f'{user_obj.full_name} already follows {company_obj.name}')
                    return redirect('add_company_follower')
                else:
                    existing_follower.status = '1'
                    existing_follower.updated_at = timezone.now()
                    existing_follower.save()
                    messages.success(request, f'{user_obj.full_name} is now following {company_obj.name} again!')
            else:
                new_follower = company_followers(
                    user = user_obj,
                    company = company_obj,
                    status = '1'
                )
                new_follower.save()
                messages.success(request, f'Successfully added {user_obj.full_name} as follower of {company_obj.name}')
                print(f'Successfully added {user_obj.full_name} as follower of {company_obj.name}')

            return redirect ('company_followers_list')
        
        except Exception as e:
            messages.error(request, f'Error adding follower:{str(e)}')
            return redirect('add_company_follower')
        
    available_users = user.objects.exclude(status='5').exclude(role='0')
    for usr in available_users:
        usr.md5_id = encrypt_id(usr.id)
    
    context={
        'current_user': user.objects.get(id=request.session.get('user_id')),
        'users': available_users,  
        'companies':[]
    }
    return render(request, 'add_company_follower.html', context)


@super_admin_required
def unfollow_company(request, encrypted_id):
    try:
        follower = get_company_follower_by_encrypted_id(encrypted_id)
        
        if not follower:
            messages.error(request, 'Follower relationship not found!')
            return redirect('company_followers_list')
        
        user_name = follower.user.full_name
        company_name = follower.company.name
        
        follower.status = '0'
        follower.updated_at = timezone.now()
        follower.save()
        
        messages.warning(request, f'{user_name} has unfollowed {company_name}')
        
    except Exception as e:
        messages.error(request, f'Error unfollowing company: {str(e)}')
    
    return redirect('company_followers_list')

@super_admin_required
def job_posts_list(request):
    context = {
        'current_user': user.objects.get(id=request.session.get('user_id'))
    }
    return render (request, 'job_posts_list.html', context)


@super_admin_required
def job_posts_data(request):
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')

        queryset = job_posts.objects.exclude(status='5').select_related('company')

        if search_value:
            queryset = queryset.filter(
                Q(job_title__icontains=search_value) |
                Q(requirements__icontains=search_value) |
                Q(salary_range__icontains=search_value) |
                Q(company__name__icontains=search_value) |
                Q(location__icontains=search_value) |
                Q(employment_type__icontains=search_value)
            )

        records_total = job_posts.objects.exclude(status='5').count()
        records_filtered = queryset.count()

        queryset = queryset.order_by('-created_at')

        paginator = Paginator(queryset, length)
        page_number = start // length + 1
        page = paginator.get_page(page_number)

        data = []
        for job in page:
            company_md5 = encrypt_id(job.company.id)
            job_md5 = encrypt_id(job.id)

            data.append({
                "job_title": job.job_title,
                "company_name": f"<a href='/companies/details/{company_md5}/'>{job.company.name}</a>",
                "location": job.location or "Not specified",
                "employment_type": job.get_employment_type_display(),
                "salary_range": job.salary_range or "Not specified",
                "requirements": job.requirements or "Not specified",
                "posted_on": job.created_at.strftime('%Y-%m-%d'),
                "actions": f"""
                    <div class='btn-group'>
                        <a href='/job_posts/details/{job_md5}/' class='btn btn-sm btn-primary' title="View Details">
                            <i class='fas fa-eye'></i>
                        </a>

                        <a href='/job_posts/edit/{job_md5}/' class='btn btn-sm btn-warning'>
                            <i class='fas fa-edit'></i>
                        </a>
                        <a href='/job_posts/delete/{job_md5}/' class='btn btn-sm btn-danger' 
                           onclick="return confirm('Are you sure you want to delete this job post?')">
                            <i class='fas fa-trash'></i>
                        </a>
                    </div>
                """
            })

        response_data = {
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": data
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            "draw": 1,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)
        })





@super_admin_required
def add_job_post(request):
    if request.method == "POST":
        try:
            company_id = request.POST.get('company_id')
            job_title = request.POST.get('job_title')
            job_description = request.POST.get('job_description')
            requirements = request.POST.get('requirements')
            location = request.POST.get('location')
            salary_range = request.POST.get('salary_range')
            employment_type = request.POST.get('employment_type')

            if not company_id or not job_title:
                messages.error(request, 'Company and Job Title are required.')
                return redirect('add_job_post')
            
            company_obj = get_company_by_encrypted_id(company_id)
            
            new_job_post = job_posts(
                company=company_obj,
                job_title=job_title,
                job_description=job_description,
                requirements=requirements,
                location=location,
                salary_range=salary_range,
                employment_type=employment_type
            )
            new_job_post.save()
            messages.success(request, f'Job post "{job_title}" added successfully!')
            return redirect('job_posts_list')

        except Exception as e:
            print(request, f'Error adding job post: {str(e)}')
            messages.error(request, f'Error adding job post: {str(e)}')
            return redirect('add_job_post')
        
    available_companies = company.objects.exclude(status='5')
    for comp in available_companies:
        comp.md5_id = encrypt_id(comp.id)

    context = {
        'current_user': user.objects.get(id=request.session.get('user_id')),
        'companies': available_companies,
        'employment_types': job_posts.EMPLOYMENT_TYPE_CHOICES
    }
    return render(request, 'add_job_post.html', context)


@super_admin_required
def job_post_details(request, encrypted_id):
    job_post = get_job_post_by_encrypted_id(encrypted_id)
    
    if not job_post:
        messages.error(request, 'Job post not found!')
        return redirect('job_posts_list')
    
    job_post.md5_id = encrypt_id(job_post.id)
    company_md5 = encrypt_id(job_post.company.id)
    
    context = {
        'job_post': job_post,
        'company_md5': company_md5,
        'current_user': user.objects.get(id=request.session.get('user_id'))
    }
    
    return render(request, 'job_post_details.html', context)


@super_admin_required
def edit_job_post(request, encrypted_id):
    job_post = get_job_post_by_encrypted_id(encrypted_id)
    
    if not job_post:
        messages.error(request, 'Job post not found!')
        return redirect('job_posts_list')
    
    if request.method == "POST":
        try:
            company_id = request.POST.get('company_id')
            job_title = request.POST.get('job_title')
            job_description = request.POST.get('job_description')
            requirements = request.POST.get('requirements')
            location = request.POST.get('location')
            salary_range = request.POST.get('salary_range')
            employment_type = request.POST.get('employment_type')

            company_obj = get_company_by_encrypted_id(company_id)

            job_post.company = company_obj
            job_post.job_title = job_title
            job_post.job_description = job_description
            job_post.requirements = requirements
            job_post.location = location
            job_post.salary_range = salary_range
            job_post.employment_type = employment_type
            job_post.updated_at=timezone.now()
            job_post.save()

            messages.success(request, f'Job post "{job_title}" updated successfully!')
            return redirect('job_posts_list')

        except Exception as e:
            print(f'Error updating job post: {str(e)}')
            messages.error(request, f'Error updating job post: {str(e)}')
            return redirect('edit_job_post', encrypted_id=encrypted_id)

    available_companies = company.objects.exclude(status='5')
    for comp in available_companies:
        comp.md5_id = encrypt_id(comp.id)

    context = {
        'current_user': user.objects.get(id=request.session.get('user_id')),
        'job_post': job_post,
        'companies': available_companies,
        'employment_types': job_posts.EMPLOYMENT_TYPE_CHOICES
    }
    return render(request, 'edit_job_post.html', context)

@super_admin_required 
def delete_job_post(request, encrypted_id):
    job_post = get_job_post_by_encrypted_id(encrypted_id)

    try:
        job_title = job_post.job_title
        job_post.status ='5'
        job_post.save()

        messages.success(request, f'Job post "{job_title}" deleted successfully!')
        print(f'Job post "{job_title}" deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting job post: {str(e)}')
        print(f'Error deleting job post: {str(e)}')
    
    return redirect('job_posts_list')
