from django.contrib import admin

# Register your models here.
from login.models import User,ConfirmString,ClickHistory,ConnectHistory
admin.site.register(User)
admin.site.register(ConfirmString)

@admin.register(ClickHistory)
class ClickHistoryAdmin(admin.ModelAdmin):
    list_display = ["clicknet_areaname","clicknet_date"]
    search_fields = ("clicknet_date",)
    # ordering = 设置以clicknet_date作为排序条件
    ordering = ("clicknet_date",)
    # list_per_page = 设置每页显示的字段数
    list_per_page = 10

@admin.register(ConnectHistory)
class ConnectHistoryAdmin(admin.ModelAdmin):
    list_display = ["connectnet_areaname","connectnet_date"]
    search_fields = ("connectnet_date",)
    # ordering = 设置以connectnet_date作为排序条件
    ordering = ("connectnet_date",)
    # list_per_page = 设置每页显示的字段数
    list_per_page = 10