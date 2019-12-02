import os
from django.core.mail import EmailMultiAlternatives

os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite2.settings'

if __name__ == '__main__':

    subject, from_email, to = '工资条', '17611391232m@sina.cn', 'liuchenglong@ezhangxiu.com'
    text_content = '本月发放工资200000'
    html_content = '<p>本月发放工资20000</p>'
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
# import os
# from django.core.mail import send_mail
#
# os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite2.settings'
#
# if __name__ == '__main__':
#
#     send_mail(
#         '来自www.liujiangblog.com的测试邮件',
#         '欢迎访问www.liujiangblog.com，这里是刘江的博客和教程站点，本站专注于Python、Django和机器学习技术的分享！',
#         '17611391232m@sina.cn',
#         ['1060369355@qq.com'],
#     )