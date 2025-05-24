from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from inventory.models import Store

class UserProfile(models.Model):
    """Profile model for extending the built-in Django User model with additional fields"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='assigned_staff',
                              help_text="Store this staff member is assigned to. Leave blank for admins or staff with access to all stores.")
    phone = models.CharField(max_length=20, blank=True)
    position = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

    def has_full_access(self):
        """Check if user has admin privileges or is not assigned to a specific store"""
        return self.user.is_superuser or self.user.is_staff and self.store is None

    def get_accessible_stores(self):
        """Get list of stores this user can access"""
        if self.has_full_access():
            return Store.objects.all()
        elif self.store:
            return Store.objects.filter(id=self.store.id)
        return Store.objects.none()

# Signal to create a UserProfile whenever a User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        # In case the profile doesn't exist yet
        UserProfile.objects.create(user=instance)