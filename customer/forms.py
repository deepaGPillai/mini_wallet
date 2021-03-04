from django.contrib.auth.forms import UserCreationForm

from customer.models import Customer


class CreateCustomerForm(UserCreationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields['password2']  # Removing password2 to avoid password confirmation while registering

    class Meta:
        model = Customer
        fields = ['username', 'password1', 'email']
