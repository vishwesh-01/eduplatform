"""
certificates/routes.py — Certificate list and PDF download endpoints.

Endpoints:
    GET /api/v1/certificates                          — List learner's certificates
    GET /api/v1/certificates/<code>/download          — Download PDF (ownership enforced)
"""

from io import BytesIO

from flask import send_file
from flask_jwt_extended import get_jwt_identity, jwt_required

from ...app import error_response, success_response
from ...extensions import db
from ...models import Certificate, Course, User
from . import certificates_bp
from .services import generate_certificate_pdf


@certificates_bp.route("", methods=["GET"])
@jwt_required()
def list_certificates():
    """
    Return all certificates earned by the authenticated learner.

    Returns:
        200: { certificates: [...] }
    """
    user_id = get_jwt_identity()
    certs = Certificate.query.filter_by(user_id=user_id).all()

    data = []
    for c in certs:
        course = db.session.get(Course, str(c.course_id))
        data.append({
            "id":               str(c.id),
            "certificate_code": str(c.certificate_code),
            "course_id":        str(c.course_id),
            "course_title":     course.title if course else "Unknown",
            "issued_at":        c.issued_at.isoformat() if c.issued_at else None,
        })

    return success_response({"certificates": data})


@certificates_bp.route("/<certificate_code>/download", methods=["GET"])
@jwt_required()
def download_certificate(certificate_code):
    """
    Stream a PDF certificate if it belongs to the authenticated learner.

    Path param:
        certificate_code (str): UUID of the certificate

    Returns:
        200: PDF file stream (application/pdf)
        403: Certificate does not belong to caller
        404: Certificate not found
    """
    user_id = get_jwt_identity()

    cert = Certificate.query.filter_by(certificate_code=certificate_code).first()
    if cert is None:
        return error_response(404, "NOT_FOUND", "Certificate not found.")

    # Ownership check — must return 403 (not 404) per requirements
    if str(cert.user_id) != user_id:
        return error_response(403, "FORBIDDEN", "You do not own this certificate.")

    user   = db.session.get(User, user_id)
    course = db.session.get(Course, str(cert.course_id))

    if user is None or course is None:
        return error_response(404, "NOT_FOUND", "User or course data not found.")

    completion_date = (
        cert.issued_at.strftime("%d %B %Y") if cert.issued_at else "Unknown Date"
    )

    pdf_bytes = generate_certificate_pdf(
        learner_name    = user.name,
        course_title    = course.title,
        completion_date = completion_date,
        cert_code       = str(cert.certificate_code),
    )

    return send_file(
        BytesIO(pdf_bytes),
        mimetype        = "application/pdf",
        as_attachment   = True,
        download_name   = f"certificate-{certificate_code}.pdf",
    )
