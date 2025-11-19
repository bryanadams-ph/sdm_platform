from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.management import call_command
from django.db.migrations.recorder import MigrationRecorder
from django.db.models import QuerySet
from django.http import HttpResponse
from django.http import JsonResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView

from sdm_platform.users.models import User


@csrf_exempt
@require_POST
def migrate(request):
    """
    User does not need to be authenticated, but they need to have an authorization token
    """
    authorization_token = request.headers.get("Authorization")
    if authorization_token != settings.SINGLE_CD_AUTHORIZATION_TOKEN:
        return HttpResponse(status=403)
    # Run all commands that should only be run once per deployment
    call_command("migrate", interactive=False)
    last_migration = MigrationRecorder.Migration.objects.latest("id")
    return JsonResponse({"app": last_migration.app, "name": last_migration.name})


def collectstatic(request):
    authorization_token = request.headers.get("Authorization")
    if authorization_token != settings.SINGLE_CD_AUTHORIZATION_TOKEN:
        return HttpResponse(status=403)
    # Make sure you have an S3 bucket set up. AWS injects an IAM user here
    # automatically (from our tutorial).
    call_command("collectstatic", interactive=False)
    return HttpResponse(status=200)


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "id"
    slug_url_kwarg = "id"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self) -> str:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.get_absolute_url()  # pyright: ignore[reportAttributeAccessIssue]

    def get_object(self, queryset: QuerySet | None = None) -> User:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user  # pyright: ignore[reportReturnType]


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        return reverse("users:detail", kwargs={"pk": self.request.user.pk})


user_redirect_view = UserRedirectView.as_view()
