from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings
from recipe.models import Recipe

class CoreUserManager(BaseUserManager):
    """Custom user manager for the CoreUser model"""

    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return a new CoreUser"""

        if not email:
            raise ValueError('Please enter an email address')
        
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create a superuser using above method and grant privileges"""

        user = self.create_user(email=email, password=password, **extra_fields)
        user.is_staff = True
        user.is_superuser = True

        user.save(using=self._db)
        return user

class CoreUser(AbstractBaseUser, PermissionsMixin):
    """Model to represent user in the system"""

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    # You should add custom related_name values to avoid clashes with the User model
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='core_user_groups',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='core_user_permissions',
        blank=True
    )

    objects = CoreUserManager()

    def __str__(self):
        return self.email

class Recipe(models.Model):
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes_by_user'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    link = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.title
