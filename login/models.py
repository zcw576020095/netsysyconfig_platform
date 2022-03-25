from django.db import models

# Create your models here.


class User(models.Model):
    gender = (
        ('male',"男"),
        ('female',"女")
    )
    name = models.CharField(max_length=128,unique=True)
    password = models.CharField(max_length=256)
    email = models.EmailField(unique=True)
    sex = models.CharField(max_length=32, choices=gender,default="男")
    create_time = models.DateTimeField(auto_now_add=True)
    has_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-create_time"]
        verbose_name = "用户"
        verbose_name_plural = "用户"


class ConfirmString(models.Model):
    code = models.CharField(max_length=256)
    user = models.OneToOneField('User',on_delete=models.CASCADE)
    create_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.name + ": " + self.code

    class Meta:
        ordering = ["-create_time"]
        verbose_name = "确认码"
        verbose_name_plural = "确认码"


## 断网记录
class ClickHistory(models.Model):

    clicknet_areaname = models.CharField(max_length=128,verbose_name='断网区域')
    clicknet_date = models.DateTimeField(max_length=64,verbose_name="断网时间")


    def __str__(self):
        return '{} {}'.format(self.clicknet_areaname,self.clicknet_date)

    class Meta:
        db_table = 'click_history'
        ordering = ["-clicknet_date"]
        verbose_name = "断网记录"
        verbose_name_plural = "断网记录"

## 联网记录
class ConnectHistory(models.Model):

    connectnet_areaname = models.CharField(max_length=128,verbose_name='联网区域')
    connectnet_date = models.DateTimeField(max_length=64,verbose_name="联网时间")


    def __str__(self):
        return '{} {}'.format(self.connectnet_areaname,self.connectnet_date)

    class Meta:
        db_table = 'connect_history'
        ordering = ["-connectnet_date"]
        verbose_name = "联网记录"
        verbose_name_plural = "联网记录"