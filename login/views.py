from django.shortcuts import render,redirect,HttpResponse
from .models import User,ConfirmString,ClickHistory,ConnectHistory
from .forms import UserForm
from .forms import RegisterForm
import hashlib
import datetime
import requests,json
from django.conf import settings
from django.contrib import messages

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


import logging

# 获得logger实例
logger = logging.getLogger('django')

def index(request):
    """主页视图"""
    if request.method == 'POST':
        click_data = {      ## 断网传参
            "name": "vlanif1000",
            "status": "down"
        }
        connect_data = {    ## 联网传参
            "name": "vlanif1000",
            "status": "up"
        }
        ## headers中添加上content-type这个参数，指定为json格式
        headers = {'Content-Type': 'application/json'}
        try:
            area_name = request.POST.get('net_area')
            button_value = request.POST.get('click')
            if button_value == '断网':
                clickhistory = ClickHistory.objects.create(clicknet_areaname=area_name,clicknet_date=datetime.datetime.now())
                logger.info('点击按钮value：{}'.format(button_value))
                logger.info('断网区域名称：{}'.format(area_name))
                try:
                    response = requests.put(
                        url='https://111.111.111.111:58443/api/v2/cmdb/system/interface/vlanif1000?access_token=1234234234233',
                        headers=headers, data=json.dumps(click_data),
                        verify=False)
                except Exception as send_clickreq_failed:
                    logger.info(send_clickreq_failed)
                    do_failed_email()
                    messages.success(request, '系统异常')
                result = json.dumps(json.loads(response.text), indent=4)
                if json.loads(result)['status'] == 'success' and json.loads(result)['http_status'] == 200:
                    logger.info('断网接口api调用成功success')
                    messages.success(request, '断网成功')
                    clickhistory.save()
                    logger.info('接口返回信息：{}'.format(result))
                    click_success_email()  ## 发送断网成功的通知邮件
                else:
                    logger.info('断网接口api调用失败failed')
                    messages.success(request, '断网失败，请联系网络管理员和系统维护人员！！！')
                    logger.info(result)
                    do_failed_email()  ## 平台操作失效邮件
            elif button_value == '联网':
                connecthistory = ConnectHistory.objects.create(connectnet_areaname=area_name,connectnet_date=datetime.datetime.now())
                logger.info('点击按钮value：{}'.format(button_value))
                logger.info('联网区域名称：{}'.format(area_name))
                try:
                    response = requests.put(
                        url='https://111.111.111.111:58443/api/v2/cmdb/system/interface/vlanif1000?access_token=1234234234233',
                        headers=headers, data=json.dumps(connect_data),
                        verify=False)
                except Exception as send_connectreq_failed:
                    logger.info(send_connectreq_failed)
                    do_failed_email()
                result = json.dumps(json.loads(response.text), indent=4)
                if json.loads(result)['status'] == 'success' and json.loads(result)['http_status'] == 200:
                    logger.info('联网接口api调用成功success')
                    messages.success(request, '联网成功')
                    connecthistory.save()
                    logger.info(result)
                    connect_success_email()  ## 发送联网成功的通知邮件
                else:
                    logger.info('联网接口api调用失败failed')
                    messages.success(request, '联网失败,请联系网络管理员和系统维护人员！！！')
                    do_failed_email()   ## 平台操作失效邮件
                    logger.info(result)
        except Exception as e:
            do_failed_email()  ## 平台操作失效邮件
            logger.error(e)
    return render(request,'index.html',locals())



def login(request):
    """登录视图"""
    if request.session.get('is_login',None):
        logger.info(request)
        return redirect("/index/")
    if request.method == "POST":
        login_form = UserForm(request.POST)
        message = "请检查填写的内容！"
        if login_form.is_valid():
            username = login_form.cleaned_data['username']
            password = login_form.cleaned_data['password']
            try:
                user = User.objects.get(name=username)
                if not user.has_confirmed:
                    message = '该用户还未通过邮件确认!'
                    return render(request,'login.html',locals())
                if user.password == hash_code(password): #哈希值和数据库内的值进行比较
                    request.session['is_login'] = True
                    request.session['user_id'] = user.id
                    request.session['user_name'] = user.name
                    return redirect('/index/')
                else:
                    message = "密码不正确！"
            except:
                message = "用户名不存在！"
        return render(request,'login.html',locals())
    login_form = UserForm()
    return render(request,'login.html',locals())


def logout(request):
    """登出视图"""
    if not request.session.get('is_login',None):
        return redirect("/index/")
    request.session.flush()
    return redirect("/index/")


def register(request):
    """注册视图"""
    if request.session.get('is_login',None):
        #登录状态不允许注册
        return redirect("/index/")
    if request.method == "POST":
        register_form = RegisterForm(request.POST)
        message = "请检查填写的内容！"
        if register_form.is_valid():
            username = register_form.cleaned_data['username']
            password1 = register_form.cleaned_data['password1']
            password2 = register_form.cleaned_data['password2']
            email = register_form.cleaned_data['email']
            sex = register_form.cleaned_data['sex']
            if password1 != password2:
                message = "两次输入的密码不同！"
                return render(request,'register.html',locals())
            else:
                same_name_user = User.objects.filter(name=username)
                if same_name_user: #用户名唯一
                    message = '用户名已经存在，请重新选择用户名！'
                    return render(request,'register.html',locals())
                same_email_user = User.objects.filter(email=email)
                if same_email_user: #邮箱地址唯一
                    message = '该邮箱地址已被注册，请使用别的邮箱！'
                    return render(request,'register.html',locals())
                new_user = User()
                new_user.name = username
                new_user.password = hash_code(password1)#使用加密密码
                new_user.email = email
                new_user.sex = sex
                new_user.save()
                code = make_confirm_string(new_user)
                send_email(email,code)
                return redirect('/login/') #自动跳转到登录页面
        else:
            return render(request,'register.html',locals())
    register_form = RegisterForm()
    return render(request,'register.html',locals())


def hash_code(s,salt='mysite'):
    """hash密码加密"""
    h = hashlib.sha256()
    s += salt
    h.update(s.encode())
    return h.hexdigest()


def make_confirm_string(user):
    """生成邮箱验证码"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    code = hash_code(user.name, now)
    ConfirmString.objects.create(code=code, user=user)
    return code





def send_email(email,code):
    """注册发送邮件"""
    from django.core.mail import EmailMultiAlternatives
    subject = "来自网络设备管理平台的账号激活确认邮件！"
    text_content = "谢谢各位！"
    html_content = '''<p>注册确认链接<a href="https://{}/confirm/?code={}" target=blank>https://www.baidu.com</a>,测试邮件！</p>
                      <p>请点击上方链接完成注册确认！</p>
                      <p>此链接有效期为{}天！</p>
                      '''.format('127.0.0.1.vip:5000',code,settings.CONFIRM_DAYS)


    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def click_success_email():
    """断网成功通知邮件"""
    from django.core.mail import EmailMultiAlternatives
    subject, from_email, to = '断网通知邮件', 'test@test.com', ['test@163.com']
    text_content = '网络设备管理平台-断网通知邮件'
    html_content = '<p>亦庄机房区域下行网络连接已人为中断，网络管理员，请注意！！！</p>'
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def connect_success_email():
    """联网成功通知邮件"""
    from django.core.mail import EmailMultiAlternatives
    subject, from_email, to = '断网通知邮件', 'test@test.com', ['test@163.com']
    text_content = '网络设备管理平台-联网通知邮件'
    html_content = '<p>亦庄机房区域下行网络连接已人为恢复，请各位知悉。</p>'
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def do_failed_email():
    from django.core.mail import EmailMultiAlternatives
    subject, from_email, to = '断网通知邮件', 'test@test.com', ['test@163.com']
    text_content = '网络设备管理平台-平台操作失效邮件'
    html_content = '<p>网络设备管理平台操作亦庄机房区域网络断网或联网失败，请网络管理员与系统维护人员快速排查问题！！！</p>'
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()



def user_confirm(request):
    """邮箱注册激活"""
    code = request.GET.get('code',None)
    message = ''
    try:
        confirm = ConfirmString.objects.get(code=code)
    except:
        message = '无效的确认请求！'
        return render(request,'confirm.html',locals())

    create_time = confirm.create_time
    now = datetime.datetime.now()
    if now > create_time + datetime.timedelta(settings.CONFIRM_DAYS):
        confirm.user.delete()
        message = '您的邮件已经过期！请重新注册！'
        return render(request,'confirm.html',locals())
    else:
        confirm.user.has_confirmed = True
        confirm.user.save()
        confirm.delete()
        message = '感谢确认，请使用账户登录！'
        return render(request,'confirm.html',locals())
