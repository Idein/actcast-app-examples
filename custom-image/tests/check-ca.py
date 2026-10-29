"""Offline CA checks for a completed custom image (no private keys or network)."""
import hashlib
import os
from pathlib import Path
import ssl
import subprocess

import pip._vendor.certifi as certifi
from pip._internal.commands import create_command


FIXTURES = Path(__file__).parent / "certificates"
BUNDLE = "/etc/ssl/certs/ca-certificates.crt"
assert os.environ["SSL_CERT_FILE"] == BUNDLE
assert os.environ["PIP_CERT"] == BUNDLE


def fingerprint(pem):
    return hashlib.sha256(ssl.PEM_cert_to_DER_cert(pem)).hexdigest()


blocked = {
    fingerprint((FIXTURES / name).read_text())
    for name in ["emSign_ECC_Root_CA_-_G3.crt", "Comodo_AAA_Services_root.crt"]
}
amazon = fingerprint((FIXTURES / "Amazon_Root_CA_1.pem").read_text())
for name, context in [
    ("Python default", ssl.create_default_context()),
    ("pip vendored certifi", ssl.create_default_context(cafile=certifi.where())),
]:
    roots = {
        hashlib.sha256(cert).hexdigest()
        for cert in context.get_ca_certs(binary_form=True)
    }
    assert not roots & blocked, name + " still trusts an affected root"
    assert amazon in roots, name + " lost Amazon Root CA 1"
    print(name + ": affected roots absent; Amazon Root CA 1 retained")

command = create_command("install")
options, _ = command.parse_args([])
with command._build_session(options) as session:
    assert session.verify == BUNDLE, "pip is not using PIP_CERT"

certs = sorted((FIXTURES / "cross-signed").glob("*.pem"))
assert len(certs) == 6
for cert in certs:
    result = subprocess.run(
        ["openssl", "verify", "-CAfile", BUNDLE, str(cert)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0, cert.name + " was accepted"
    assert "error 20 " in result.stderr, result.stderr
    print(cert.name + ": rejected (unknown issuer)")
subprocess.run(
    ["openssl", "verify", "-CAfile", BUNDLE, str(FIXTURES / "Amazon_Root_CA_1.pem")],
    check=True,
)
