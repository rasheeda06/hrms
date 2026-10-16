from django.urls import path

from timesheets import views

app_name = "timesheets"

urlpatterns = [
    path("", views.admin_timeline, name="timeline"),
    path("timeline/", views.admin_timeline, name="admin_timeline"),
    path("save/", views.save_timesheet, name="save_timesheet"),
    path("add-task/", views.add_task_entry, name="add_task_entry"),
    path("delete-row/<int:row_id>/", views.delete_task_row, name="delete_task_row"),
    path("copy-last-week/", views.copy_last_week, name="copy_last_week"),
    path("update-cell/", views.update_cell, name="update_cell"),
]
