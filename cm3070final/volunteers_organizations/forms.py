from django import forms
from .models import Volunteer, Organization

class VolunteerForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, required=True, label='First Name')
    last_name = forms.CharField(max_length=100, required=True, label='Last Name')
    dob = forms.DateField(
        required=True,
        label='Date of Birth',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    bio = forms.CharField(max_length=500, required=False, label='Bio')
    profile_img = forms.ImageField(required=False, label='Profile Image')

    class Meta:
        model=Volunteer
        fields = ['first_name', 'last_name', 'dob', 'bio', 'profile_img']

    def clean_dob(self):
        dob = self.cleaned_data.get('dob')
        if dob.year < 1900 or dob.year > 2010:
            raise forms.ValidationError("Invalid Date of Birth")
        return dob
    
    def __init__(self, *args, **kwargs):
        super(VolunteerForm, self).__init__(*args, **kwargs)
        for fieldname, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full text-2xl p-3 border border-gray-700 rounded bg-primary text-white',
                'placeholder': field.label + ' (Required)' if field.required else field.label
            })
            field.label = ''
        
    def save(self, account=None, commit=True):
        volunteer = super().save(commit=False)
        if account:
            volunteer.account = account
        if commit:
            volunteer.save()
        return volunteer

class OrganizationForm(forms.ModelForm):
    organization_name = forms.CharField(max_length=100, required=True, label='Organization Name')
    organization_description = forms.CharField(max_length=500, required=False, label='Description')
    street_number = forms.CharField(max_length=10, required=False, label='Street Number')
    route = forms.CharField(max_length=100, required=False, label='Street Name')
    locality = forms.CharField(max_length=100, required=False, label='City/Town')
    postal_code = forms.CharField(max_length=10, required=False, label='Postal Code')
    state = forms.CharField(max_length=100, required=False, label='State')
    state_code = forms.CharField(max_length=10, required=False, label='State Code')
    country = forms.CharField(max_length=100, required=False, label='Country')
    organization_website = forms.URLField(max_length=255, required=False, label='Organization Website')
    organization_profile_img = forms.ImageField(required=False, label='Profile Image')

    class Meta:
        model=Organization
        fields = ['organization_name', 'organization_description', 'organization_address', 'organization_website', 'organization_profile_img']

    def __init__(self, *args, **kwargs):
        super(OrganizationForm, self).__init__(*args, **kwargs)
        for fieldname, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full text-2xl p-3 border border-gray-700 rounded bg-primary text-white',
                'placeholder': field.label + ' (Required)' if field.required else field.label
            })
            field.label = ''

    def save(self, account=None, commit=True):
        organization = super().save(commit=False)

        # Merge all fields to create the 'raw' address
        address_components = [
            self.cleaned_data.get('street_number', ''),
            self.cleaned_data.get('route', ''),
            self.cleaned_data.get('locality', ''),
            self.cleaned_data.get('state_code', ''),
            self.cleaned_data.get('postal_code', ''),
            self.cleaned_data.get('country', '')
        ]
        raw_address = ", ".join(filter(None, address_components))

        # Create the structured address dictionary
        organization_address = {
            'raw': raw_address,
            'street_number': self.cleaned_data.get('street_number', ''), # ('') if None,
            'route': self.cleaned_data.get('route', ''),
            'locality': self.cleaned_data.get('locality', ''),
            'postal_code': self.cleaned_data.get('postal_code', ''),
            'state': self.cleaned_data.get('state', ''),
            'state_code': self.cleaned_data.get('state_code', ''),
            'country': self.cleaned_data.get('country', ''),
            'country_code': self.cleaned_data.get('country_code', ''),
        }

        organization.organization_address = organization_address

        if account:
            organization.account = account
        if commit:
            organization.save()
        return organization