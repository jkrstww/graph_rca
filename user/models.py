from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    自定义用户模型，扩展Django内置的用户模型
    """
    # 用户角色选项
    ROLE_CHOICES = (
        ('student', '学生'),
        ('mentor', '导师'),
        ('teacher', '老师'),
    )
    
    # 用户角色字段，默认为学生
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student', verbose_name='用户角色')
    email = models.EmailField(unique=True, verbose_name='邮箱')
    
    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
        
    def __str__(self):
        return self.username 