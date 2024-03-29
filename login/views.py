from django.shortcuts import render, redirect, HttpResponse
from . import models
from . import forms
import json
from captcha.models import CaptchaStore
from captcha.helpers import captcha_image_url
import hashlib
import datetime
from django.conf import settings
from django.utils import timezone

# Create your views here.
# hash 密码加密
def hash_code(s, salt='mysite'):
    h = hashlib.sha256()
    s += salt
    h.update(s.encode())
    return h.hexdigest()


# 邮件验证code
def make_confirm_string(user):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    code = hash_code(user.name, now)
    models.ConfirmString.objects.create(code=code, user=user)
    return code


# 首页视图
def index(request):
    if not request.session.get('is_login', None):
        return redirect('/login/')
    return render(request, 'login/index.html')
    # return render(request, 'login/index.html')


# 邮件函数
def send_email(email, code):
    from django.core.mail import EmailMultiAlternatives
    subject = '来自www.lclhyy.com的注册确认邮件'
    text_content = '''感谢您注册 www.lclhyy.com 这里是刘成龙的博客，主要是做一些自己喜欢的东西。\
        如果你看到此消息，说明你的邮箱服务器不提供HTML链接功能，请联系瓜里源
        '''
    html_content = '''
        <p>感谢注册</p><a href="http://{}/confirm/?code={}" target=blank>www.lclhyy.com</a>,\
        这里是刘成龙做的系统 专注吹牛逼
        <p>请点击此链接完成注册确认</p>
        <p>此链接的有效期为{}天！</p>
        
    '''.format('127.0.0.1:8000', code, settings.CONFIRM_DAYS)
    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


# 登录视图

def login(request):
    if request.is_ajax():
        to_json_response = dict()
        to_json_response['status'] = 1  # ajax的状态
        to_json_response['new_cptch_key'] = CaptchaStore.generate_key()
        to_json_response['new_cptch_image'] = captcha_image_url(to_json_response['new_cptch_key'])
        return HttpResponse(json.dumps(to_json_response), content_type='application/json')
    if request.session.get('is_login', None):  # 不允许重复登录
        return redirect('/index/')
    if request.method == "POST":
        # user_name = request.POST.get('username')
        # password = request.POST.get('password')
        login_form = forms.UserForm(request.POST)
        # message = "请检查填写的内容"
        # if user_name.strip() and password:
        if login_form.is_valid():
            username = login_form.cleaned_data.get('username')
            password = login_form.cleaned_data.get('password')
            try:
                user = models.User.objects.get(name=username)
            except:
                message = "用户名不存在"
                # return render(request, 'login/login.html', {'message': message})
                return render(request, 'login/login.html', locals())

            if not user.has_confirmed:
                message = "该用户邮件注册未确认！"
                return render(request, 'login/login.html', locals())
            if user.password == hash_code(password):
                request.session['is_login'] = True
                request.session['user_id'] = user.id
                request.session['user_name'] = user.name
                print(username, password)
                return redirect('/index/')
            else:
                message = "密码不正确"
                # return render(request, 'login/login.html', {'message': message})
                return render(request, 'login/login.html', locals())
        else:
            # return render(request, 'login/login.html', {'message': message})
            return render(request, 'login/login.html', locals())
    login_form = forms.UserForm()
    return render(request, 'login/login.html', locals())


# 注册视图
def register(request):
    if request.session.get('is_login', None):
        return redirect('/index/')
    if request.method == 'POST':
        register_form = forms.RegisterForm(request.POST)
        message = "请检查填写的内容"
        if register_form.is_valid():
            username = register_form.cleaned_data.get('username')
            password1 = register_form.cleaned_data.get('password1')
            password2 = register_form.cleaned_data.get('password2')
            email = register_form.cleaned_data.get('email')
            sex = register_form.cleaned_data.get('sex')
            if password1 != password2:
                message = "两次输入的密码不一致"
                return render(request, 'login/register.html', locals())
            else:
                same_name_user = models.User.objects.filter(name=username)
                if same_name_user:
                    message = "用户名已经存在"
                    return render(request, 'login/register.html', locals())
                same_email_user = models.User.objects.filter(email=email)
                if same_email_user:
                    message = "该邮箱已被注册"
                    return render(request, 'login/register.html', locals())
                # 保存到数据库
                new_user = models.User()
                new_user.name = username
                new_user.password = hash_code(password1)
                new_user.email = email
                new_user.sex = sex
                new_user.save()
                # 邮箱确认
                code = make_confirm_string(new_user)
                send_email(email, code)
                return redirect('/login/')
        else:
            return render(request, 'login/register.html', locals())
    register_form = forms.RegisterForm()
    return render(request, 'login/register.html', locals())


# 邮件确认视图

def user_confirm(request):
    code = request.GET.get('code', None)
    message = ''
    try:
        confirm = models.ConfirmString.objects.get(code=code)
    except:
        message = "无效的请求"
        return render(request, 'login/confirm.html', locals())

    c_time = confirm.c_time
    now = timezone.now()
    if now > c_time+datetime.timedelta(settings.CONFIRM_DAYS):
        confirm.user.delete()
        message = "您的邮件已经过期，请重新注册！"
        return render(request, 'login/login.html', locals())
    else:
        confirm.user.has_confirmed = True
        confirm.user.save()
        confirm.delete()
        message = "感谢确认，请使用您的账户登录"
        return render(request, 'login/confirm.html', locals())

# ajax 刷新验证码
def refresh_captcha(request):
    to_json_response = dict()
    to_json_response['status'] = 1  # ajax的状态
    to_json_response['new_cptch_key'] = CaptchaStore.generate_key()
    to_json_response['new_cptch_image'] = captcha_image_url(to_json_response['new_cptch_key'])
    return HttpResponse(json.dumps(to_json_response), content_type='application/json')


# 登出视图
def logout(request):
    if not request.session.get('is_login', None):
        # 如果本来就未登录，也就没有登出一说
        return redirect("/login/")
    request.session.flush()
    return redirect('/login/')
