"""Forms for service requests."""

from django import forms

from .models import ServiceRequest


class ServiceRequestForm(forms.ModelForm):
    """Form for creating a new service request (employee-facing)."""

    class Meta:
        model = ServiceRequest
        fields = ['category', 'description', 'location', 'urgency', 'attachment']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Jelaskan detail kebutuhan Anda...',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: Gedung A, Lantai 3',
            }),
            'urgency': forms.Select(attrs={'class': 'form-select'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    ALLOWED_EXTENSIONS = [
        'jpg', 'jpeg', 'png', 'gif', 'webp',
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'txt',
    ]

    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            # Limit file size to 10 MB
            if attachment.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Ukuran file maksimal 10MB.')
            # Validate file extension
            ext = attachment.name.rsplit('.', 1)[-1].lower() if '.' in attachment.name else ''
            if ext not in self.ALLOWED_EXTENSIONS:
                allowed = ', '.join(self.ALLOWED_EXTENSIONS)
                raise forms.ValidationError(
                    f'Tipe file tidak diizinkan. Tipe yang diizinkan: {allowed}'
                )
        return attachment


class StatusUpdateForm(forms.Form):
    """Form for GA / Manager to update request status."""

    STATUS_CHOICES = [
        ('verified', 'Verified'),
        ('on_progress', 'On Progress'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    new_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Status Baru',
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Catatan perubahan status...',
        }),
        label='Catatan',
    )
