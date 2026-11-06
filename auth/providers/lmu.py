import html

from auth.providers.base import SSOProvider
from utils.helpers import extract_html_value

# Shibboleth "local storage" probe fields the IdP posts back on its first page.
_LS_FIELDS = {
    'shib_idp_ls_exception.shib_idp_session_ss': '',
    'shib_idp_ls_success.shib_idp_session_ss': 'true',
    'shib_idp_ls_value.shib_idp_session_ss': '',
    'shib_idp_ls_exception.shib_idp_persistent_ss': '',
    'shib_idp_ls_success.shib_idp_persistent_ss': 'true',
    'shib_idp_ls_value.shib_idp_persistent_ss': '',
    'shib_idp_ls_supported': 'true',
    '_eventId_proceed': '',
}

_CSRF_RE = r'name="csrf_token" value="([^"]+)"'


class LMUProvider(SSOProvider):
    """SSO provider for Ludwig-Maximilians-Universität München (LMU).

    anny routes the domain ``lmu.de`` to the LMU Shibboleth IdP hosted by the
    LRZ (``lmuidp.lrz.de``): a local-storage probe page, then the
    username/password form. Log in with your LMU campus ID (or LMU e-mail).
    """

    name = "LMU"
    domain = "lmu.de"
    available_days_ahead = 4

    def authenticate(self) -> str:
        self.session.headers.pop('x-requested-with', None)
        self.session.headers.pop('x-inertia', None)
        self.session.headers.pop('x-inertia-version', None)

        # anny answers the federation URL with 409 while Inertia headers are
        # present; re-fetch it as a plain browser request to reach the IdP.
        idp_page = self.redirect_response
        if 'csrf_token' not in idp_page.text:
            idp_page = self.session.get(idp_page.url)

        # Step 1: local-storage probe page (execution=e1s1)
        csrf_token = extract_html_value(idp_page.text, _CSRF_RE)
        response = self.session.post(
            idp_page.url,
            data={'csrf_token': csrf_token, **_LS_FIELDS},
        )

        old_referer = self.session.headers.get('referer')
        self.session.headers['referer'] = response.url

        # Step 2: credentials form (execution=e1s2)
        csrf_token = extract_html_value(response.text, _CSRF_RE)
        response = self.session.post(
            response.url,
            data={
                'csrf_token': csrf_token,
                'j_username': self.username,
                'j_password': self.password,
                'donotcache': '1',
                '_eventId_proceed': '',
            },
        )

        if old_referer is not None:
            self.session.headers['referer'] = old_referer

        body = html.unescape(response.text)
        if "/consume" in body:
            return response.text

        if "_shib_idp_consentIds" in body or "shib_idp_consent" in body.lower():
            raise ValueError(
                "LMU login needs a one-time consent: log in to anny.eu with LMU in a "
                "browser once, accept the attribute release, then run this again"
            )
        raise ValueError("LMU authentication failed - invalid credentials or SSO error")
