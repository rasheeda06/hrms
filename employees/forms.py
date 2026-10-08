from django import forms
from django.contrib.auth.models import Group, User

from accounts.roles import EMPLOYEE_GROUP
from employees.models import Department, Employee


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. Finance"}
            )
        }


class EmployeeForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        help_text="Login username for this employee.",
    )
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput,
        help_text="Required when adding. Leave blank when editing to keep the current password.",
    )

    class Meta:
        model = Employee
        fields = [
            "employee_id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "department",
            "job_title",
            "date_of_joining",
            "address",
            "status",
        ]
        widgets = {
            "date_of_joining": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, is_create=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_create = is_create
        for name, field in self.fields.items():
            css = "form-select" if name in {"department", "status"} else "form-control"
            field.widget.attrs.setdefault("class", css)

        if self.instance and self.instance.pk:
            self.fields["username"].initial = self.instance.user.username
            self.fields["username"].required = False
            self.fields["username"].widget.attrs["readonly"] = True
            self.fields["password"].required = False
        else:
            self.fields["password"].required = True

    def clean_username(self):
        if self.instance.pk:
            return self.instance.user.username
        username = self.cleaned_data["username"]
        qs = User.objects.filter(username=username)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise forms.ValidationError("That username is already in use.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        qs = Employee.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("An employee with this email already exists.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if self.is_create and not password:
            raise forms.ValidationError("Enter a password for the new account.")
        return password

    def save(self, commit=True):
        employee = super().save(commit=False)
        active = employee.status == Employee.Status.ACTIVE

        if self.is_create:
            user = User.objects.create_user(
                username=self.cleaned_data["username"],
                password=self.cleaned_data["password"],
                email=employee.email,
                first_name=employee.first_name,
                last_name=employee.last_name,
                is_active=active,
            )
            group, _ = Group.objects.get_or_create(name=EMPLOYEE_GROUP)
            user.groups.add(group)
            employee.user = user
        else:
            user = employee.user
            user.first_name = employee.first_name
            user.last_name = employee.last_name
            user.email = employee.email
            user.is_active = active
            password = self.cleaned_data.get("password")
            if password:
                user.set_password(password)
            user.save()

        if commit:
            employee.save()
        return employee
