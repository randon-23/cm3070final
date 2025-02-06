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
                'class': 'w-full text-sm text-gray-800 bg-gray-100 focus:bg-transparent pl-4 pr-10 py-3.5 rounded-md outline-blue-600',
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
    country = forms.CharField(max_length=100, required=False, label='Country')
    organization_website = forms.URLField(max_length=255, required=False, label='Organization Website')
    organization_profile_img = forms.ImageField(required=False, label='Profile Image')

    class Meta:
        model=Organization
        fields = ['organization_name', 'organization_description', 'organization_website', 'organization_profile_img']

    def __init__(self, *args, **kwargs):
        super(OrganizationForm, self).__init__(*args, **kwargs)
        for fieldname, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full text-sm text-gray-800 bg-gray-100 focus:bg-transparent pl-4 pr-10 py-3.5 rounded-md outline-blue-600',
                'placeholder': field.label + ' (Required)' if field.required else field.label
            })
            field.label = ''
    
    def clean(self):
        super().clean()
        # Merge all fields to create the 'raw' address
        address_components = [
            self.cleaned_data.get('street_number', ''),
            self.cleaned_data.get('route', ''),
            self.cleaned_data.get('locality', ''),
            self.cleaned_data.get('state', ''),
            self.cleaned_data.get('postal_code', ''),
            self.cleaned_data.get('country', '')
        ]
        raw_address = ", ".join(filter(None, address_components))
        # Create the structured address dictionary
        organization_address = {
            'raw': raw_address,
            'street_number': self.cleaned_data.get('street_number', ''),
            'route': self.cleaned_data.get('route', ''),
            'locality': self.cleaned_data.get('locality', ''),
            'postal_code': self.cleaned_data.get('postal_code', ''),
            'state': self.cleaned_data.get('state', ''),
            'country': self.cleaned_data.get('country', ''),
        }
        self.cleaned_data['organization_address'] = organization_address
        self.cleaned_data.pop('street_number', None)
        self.cleaned_data.pop('route', None)
        self.cleaned_data.pop('locality', None)
        self.cleaned_data.pop('postal_code', None)
        self.cleaned_data.pop('state', None)
        self.cleaned_data.pop('country', None)

        return self.cleaned_data

    def save(self, account=None, commit=True):
        organization = super().save(commit=False)
        if account:
            organization.account = account
        organization.organization_address = self.cleaned_data['organization_address']
        if commit:
            organization.save()
        return organization