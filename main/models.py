from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User, Permission, UserManager
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django_countries.fields import CountryField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
from django.utils.html import format_html

import time
import uuid
import datetime

from .utils import Tools
from .validators import verifycode_validate
import main.constants as Constants


class Image(models.Model):
    image = models.ImageField(upload_to="images")
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name='images')
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return str(self.image)


class TLI(models.Model):
    license_no = models.CharField(
        max_length=64, unique=True, verbose_name='TourGuide No.')
    language = models.CharField(
        choices=Constants.LANGUAGE, max_length=7, default='chinese')
    date_of_expiry = models.DateField()

    staff = models.OneToOneField(
        'Staff', on_delete=models.CASCADE, related_name='TLI')

    class Meta:
        verbose_name = 'TourGuide License Infomation'
        verbose_name_plural = 'TourGuide License Info'

    def __str__(self):
        return self.license_no


class DLI(models.Model):
    driving_license_no = models.CharField(
        max_length=32, unique=True, verbose_name='Driving License No.',)
    driver_code = models.CharField(max_length=16)
    date_of_issue = models.DateField()
    date_of_expiry = models.DateField()

    staff = models.OneToOneField(
        'Staff', on_delete=models.CASCADE, related_name='DLI')

    class Meta:
        verbose_name = 'Driver License Infomation'
        verbose_name_plural = 'Driver License Info'

    def __str__(self):
        return self.driving_license_no


class PPI(models.Model):
    passport_no = models.CharField(
        max_length=32, unique=True, verbose_name='Passport No.')
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    gender = models.CharField(choices=Constants.GENDER, max_length=6, default='male')
    country = CountryField(blank_label='(select country)')
    date_of_birth = models.DateField()
    date_of_issue = models.DateField()
    date_of_expiry = models.DateField()

    staff = models.OneToOneField(
        'Staff', on_delete=models.CASCADE, related_name='PPI')

    class Meta:
        verbose_name = 'Passport Infomation'
        verbose_name_plural = 'Passport Info'

    def __str__(self):
        return self.first_name + ' ' + self.last_name


class Company(models.Model):
    name = models.CharField(max_length=128)
    tel = models.CharField(max_length=16)
    phone = models.CharField(max_length=16)
    email = models.EmailField()
    addr = models.CharField(max_length=256)
    verifycode = models.CharField(
        max_length=4, unique=True, default=Tools.get_code, help_text='For Staff Regist')

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Company'

    def __str__(self):
        return self.name


class Staff(User):
    name = models.CharField(max_length=64, unique=True, help_text='name')  # 姓名
    phone = models.CharField(max_length=16, unique=True,
                             help_text='your phone')  # 电话
    nickname = models.CharField(max_length=64, help_text='nick name')  # 昵称
    introduction = models.TextField(max_length=256, blank=True)  # 自我介绍
    photo = models.ImageField(upload_to='photos', null=True, blank=True)  # 头像
    status = models.CharField(
        max_length=16, default='enabled', blank=True, null=True, choices=Constants.STATUS)  # 状态
    hour_pay = models.FloatField(blank=True, default=0.0)  # 时薪
    work_status = models.CharField(max_length=5, default='start', choices=Constants.WORK_STATUS)
    driver = models.BooleanField(
        default=False, verbose_name='Driver ?')  # 是否 司机
    tourguide = models.BooleanField(
        default=False, verbose_name='TourGuide ?')  # 是否 导游
    company = models.OneToOneField(
        Company, on_delete=models.CASCADE, related_name='staff')

    class Meta:
        verbose_name = 'Staff'
        verbose_name_plural = 'Staff'

    def __str__(self):
        return self.name

    def save(self):
        super().save()

class VehicleModel(models.Model):
    model = models.CharField(default='Car', max_length=6, choices=Constants.MODEL)  # 类型
    name = models.CharField(max_length=64)  # 名称
    num = models.IntegerField(default=5, verbose_name='number of passenger')  # 乘坐人数
    amount = models.FloatField()  # 价格
    photo = models.ImageField(upload_to='vehicle', blank=True)  # 图片

    class Meta:
        verbose_name = 'Vehicle Model'
        verbose_name_plural = 'Vehicle Model'
    
    def __str__(self):
        return self.name

class VehicleManager(models.Manager):
    pass


class Vehicle(models.Model):
    eng_no = models.CharField(max_length=16, unique=True)               # 发动机号
    chassis_no = models.CharField(max_length=32, unique=True)           # 车架号
    traffic_plate_no = models.CharField(max_length=16, unique=True)     # 车牌号
    exp_date = models.DateField()                                       # 有效期
    reg_date = models.DateField()                                       # 注册日期
    ins_exp = models.DateField()                                        # 日期
    policy_no = models.CharField(max_length=32, unique=True)            # 保险号
    status = models.CharField(
        max_length=16, default='enabled', blank=True, null=True, choices=Constants.STATUS)
    model = models.ForeignKey(VehicleModel, on_delete=models.CASCADE, related_name='vehicle')
    company = models.OneToOneField(
        Company, on_delete=models.CASCADE, related_name='vehicle')

    objects = VehicleManager

    class Meta:
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicle'

    def __str__(self):
        return self.traffic_plate_no

class AbstractOrder(models.Model):
    order_id = models.CharField(max_length=16, default=get_random_string(length=16, allowed_chars='0123456789'))
    amount = models.FloatField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=8, default='open', choices=Constants.ORDER_STATUS)
    pay_status = models.CharField(max_length=9, default='paid', choices=Constants.PAY_STATUS)
    client_type = models.CharField(max_length=8, default='company', choices=Constants.CLIENT_TYPE)
    remake = models.TextField(blank=True, max_length=256)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.order_id

    def clean(self):
        super().clean()

        if self.start_time is not None and self.end_time is not None:
            if self.start_time > self.end_time:
                raise ValidationError('the end time must be after start time')


class OrderStaff(AbstractOrder):

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='order')
    settle_status = models.CharField(max_length=8, default='unsettle', choices=Constants.SETTLE_STATUS)
    staff_confirm = models.CharField(max_length=6, default='wait', choices=Constants.STAFF_CONFIRM)

    class Meta:
        verbose_name = 'Staff Orders'
        verbose_name_plural = 'Staff Orders'


class OrderVehicle(AbstractOrder):

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='order')
    pickup_type = models.CharField(max_length=4, default='self', choices=Constants.PICK_TYPE)

    class Meta:
        verbose_name = 'Vehicle Orders'
        verbose_name_plural = 'Vehicle Orders'
