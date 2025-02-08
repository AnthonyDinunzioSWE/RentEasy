import base64
import os
from flask import Blueprint, current_app, jsonify, request, send_file
from werkzeug.security import check_password_hash
from datetime import datetime
from .models import db, User, Tenant, Property, Payment, Invoice, LeaseAgreement
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image


api = Blueprint("api", __name__, url_prefix="/api")


# **Authentication (Login)**
@api.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    print("DATA", data)
    print("EMAIL: ", email)
    print("PASSWORD: ", password)

    user = User.query.filter_by(email=email).first()
    print("USER: ", user)
    if user and check_password_hash(user.password_hash, password):
        return jsonify({
            "message": "Login successful",
            "user_id": user.id,
            "role": user.role,
            "name": user.name,
            "email": user.email
        }), 200
    return jsonify({"message": "Invalid credentials"}), 401


# **Get Property Details for a Tenant**
@api.route("/property/<int:user_id>", methods=["GET"])
def get_property_for_tenant(user_id):
    user = User.query.get(user_id)
    tenant = Tenant.query.filter_by(user_id=user_id).first()
    if not tenant:
        return jsonify({"message": "Tenant not found"}), 404

    property_info = Property.query.get(tenant.property_id)
    if not property_info:
        return jsonify({"message": "Property not found"}), 404

    return jsonify({
        "id": property_info.id,
        "address": property_info.address,
        "unit_number": property_info.unit_number,
        "rent_amount": property_info.rent_amount,
        "status": property_info.status
    })


# **Get Rent Details for a Tenant**
@api.route("/rent/<int:tenant_id>", methods=["GET"])
def get_rent_details(tenant_id):
    tenant = Tenant.query.get(tenant_id)
    if not tenant:
        return jsonify({"message": "Tenant not found"}), 404

    lease = LeaseAgreement.query.filter_by(tenant_id=tenant_id).first()
    if not lease:
        return jsonify({"message": "Lease agreement not found"}), 404

    return jsonify({
        "property_id": lease.property_id,
        "rent_amount": lease.rent,
        "lease_start": lease.lease_start.strftime('%Y-%m-%d'),
        "lease_end": lease.lease_end.strftime('%Y-%m-%d'),
        "status": "Active" if lease.signed_status else "Pending Signature"
    })


# **Get Invoices for a Tenant**
@api.route("/invoices/<int:tenant_id>", methods=["GET"])
def get_invoices(tenant_id):
    invoices = Invoice.query.filter_by(tenant_id=tenant_id).all()
    return jsonify([
        {
            "id": inv.id,
            "amount_due": inv.amount,
            "paid_amount": inv.paid_amount,
            "due_date": inv.due_date.strftime('%Y-%m-%d'),
            "status": inv.status,
            "description": inv.description
        } for inv in invoices
    ])


# **Make a Payment (Full or Partial)**
@api.route("/payment", methods=["POST"])
def make_payment():
    data = request.get_json()
    invoice_id = data.get("invoice_id")
    tenant_id = data.get("tenant_id")
    amount_paid = data.get("amount_paid")

    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return jsonify({"message": "Invoice not found"}), 404

    if invoice.tenant_id != tenant_id:
        return jsonify({"message": "Unauthorized payment attempt"}), 403

    new_payment = Payment(
        invoice_id=invoice_id,
        tenant_id=tenant_id,
        amount_paid=amount_paid,
        payment_date=datetime.utcnow()
    )
    db.session.add(new_payment)

    invoice.paid_amount += amount_paid
    invoice.status = "Paid" if invoice.paid_amount >= invoice.amount else "Partial Payment"
    db.session.commit()

    return jsonify({"message": "Payment successful", "invoice_status": invoice.status})


@api.route("/lease/<int:user_id>", methods=["GET"])
def get_lease_agreement(user_id):
    tenant = Tenant.query.filter_by(user_id=user_id).first()
    
    if not tenant:
        return jsonify({"message": "Tenant not found for user_id: {}".format(user_id)}), 404
        
    print('tenant: ', tenant)
    
    lease = LeaseAgreement.query.filter_by(tenant_id=tenant.id).first()

    if not lease:
        return jsonify({"message": "No lease data found for tenant_id: {}".format(tenant.id)}), 404
        
    print('lease: ', lease)

    lease_data = jsonify({
    "property_address": lease.property.address,  # Change this field
    "start_date": lease.lease_start.strftime('%Y-%m-%d'),
    "end_date": lease.lease_end.strftime('%Y-%m-%d'),
    "monthly_rent": lease.rent,  # Change this field
    "status": "Signed" if lease.signed_status else "Pending Signature",
    "document_url": lease.document_url
    })
    return lease_data

@api.route("/update-profile", methods=["PUT"])
def update_profile():
    data = request.get_json()
    user_id = data.get("user_id")
    new_name = data.get("name")
    new_email = data.get("email")

    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    user.name = new_name
    user.email = new_email

    db.session.commit()

    return jsonify({"message": "Profile updated successfully", "name": user.name, "email": user.email})

@api.route("/user_profile/<int:user_id>", methods=["GET"])
def get_user_profile(user_id):
    user_id = str(user_id)
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    # Fetch the user from the database
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Prepare the response data
    user_data = {
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'created_at': user.created_at,
    }

    # Fetch tenant and property data if applicable
    tenant_data = None
    property_data = None

    #tenant = Tenant.query.filter_by(user_id=user.id).first()
    #prop = Property.query.filter_by(user_id=user.id).first()
    #if tenant: 
    #    tenant_data = {
    #        'lease_start': tenant.lease_start,
    #        'lease_end': tenant.lease_end,
    #        'signed_status': tenant.signed_status
    #    }
    #if prop:
    #    property_data = {
    #        'address': prop.address
    #    }

    # Combine all the data into a response
    response_data = {
        'user': user_data,
    #    'tenant': tenant_data,
    #    'properties': property_data
    }

    return jsonify(response_data)

@api.route("/tenant/<int:user_id>", methods=["GET"])
def get_tenant(user_id):
    tenant = Tenant.query.filter_by(user_id=user_id).first()
    if not tenant:
        return jsonify({"message": "Tenant not found"}), 404
    
    prop = Property.query.get(tenant.property_id)
    if not prop:
        return jsonify({'message': 'Property Not Found!'}), 404
    
    prop_data = jsonify({'address': prop.address,
                         'unit_number': prop.unit_number,
                         'rent_amount': prop.rent_amount})
    
    tenant_data = jsonify({"id": tenant.id,
                           "property_id": tenant.property_id,
                           "lease_start": tenant.lease_start.strftime('%Y-%m-%d'),
                           "lease_end": tenant.lease_end.strftime('%Y-%m-%d'),
                           "signed_status": tenant.signed_status,
                           "landlord_id": tenant.landlord_id,})

    return jsonify({
        "id": tenant.id,
        "property_id": tenant.property_id,
        "lease_start": tenant.lease_start.strftime('%Y-%m-%d'),
        "lease_end": tenant.lease_end.strftime('%Y-%m-%d'),
        "signed_status": tenant.signed_status,
        "landlord_id": tenant.landlord_id,
    })

@api.route('/upload_signature/<int:user_id>', methods=['POST'])
def upload_signature(user_id):
    if 'signature' not in request.files:
        return jsonify({'error': 'No signature uploaded'}), 400
    
    signature_file = request.files['signature']
    
    # Ensure 'uploads' directory exists
    upload_dir = os.path.join(current_app.root_path, 'uploads')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    # Save file
    file_path = os.path.join(upload_dir, f'{user_id}_signature.png')
    signature_file.save(file_path)

    # Retrieve user, tenant, and lease info
    tenant = Tenant.query.filter_by(user_id=user_id).first()
    lease = LeaseAgreement.query.filter_by(tenant_id=tenant.id).first()

    if lease:
        lease.tenant_signature_path = f'{user_id}_signature.png'  # Store only the filename
        db.session.commit()
        generate_lease(lease.id, tenant_signature_path=file_path)

    return jsonify({'message': 'Signature uploaded successfully', 'file_path': file_path}), 200

def generate_lease(lease_id, tenant_signature_path=None, landlord_signature_path=None):
    lease = LeaseAgreement.query.get_or_404(lease_id)
    landlord = User.query.get(lease.landlord_id)
    lease_folder = os.path.join(current_app.root_path, "leases")
    if not os.path.exists(lease_folder):
        os.makedirs(lease_folder)

    file_path = os.path.join(lease_folder, f"lease_{lease_id}.pdf")

    # Create a PDF Document
    pdf = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()
    content = []

    # Title
    title = Paragraph("<b>Residential Lease Agreement</b>", styles["Title"])
    content.append(title)
    content.append(Spacer(1, 0.2 * inch))

    # Landlord & Tenant Info
    landlord_info = f"<b>Landlord:</b> {landlord.name} <br/> <b>Tenant:</b> {lease.tenant_name}"
    property_info = f"<b>Property:</b> {lease.property_name} <br/> <b>Address:</b> {lease.property_name}"
    lease_terms = f"<b>Lease Start:</b> {lease.lease_start} <br/> <b>Lease End:</b> {lease.lease_end}"

    content.append(Paragraph(landlord_info, styles["Normal"]))
    content.append(Paragraph(property_info, styles["Normal"]))
    content.append(Paragraph(lease_terms, styles["Normal"]))
    content.append(Spacer(1, 0.3 * inch))

    # Rent Table
    rent_data = [
        ["Description", "Amount"],
        ["Monthly Rent", f"${lease.rent}"]
    ]
    table = Table(rent_data, colWidths=[250, 150])
    table.setStyle(TableStyle([ 
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    content.append(table)
    content.append(Spacer(1, 0.3 * inch))

    # Terms & Conditions
    lease_terms_text = """
    <b>Terms & Conditions:</b> The tenant agrees to follow all property rules, maintain the unit in good condition,
    and notify the landlord of any damages. Failure to pay rent on time will result in penalties.
    """
    content.append(Paragraph(lease_terms_text, styles["Normal"]))

    # Signatures section
    content.append(Spacer(1, 0.5 * inch))
    content.append(Paragraph("<b>Signatures:</b>", styles["Normal"]))
    content.append(Spacer(1, 0.2 * inch))
    if landlord_signature_path:
        landlord_signature_path = os.path.join(uploads_folder, landlord_signature_path)
        print(f"LL Sig: ", landlord_signature_path)
        # Add the tenant signature image
        content.append(Paragraph("Tenant Signature:"))
        landlord_signature = Image(landlord_signature_path, width=200, height=50)
        print(f"LL", landlord_signature)
        landlord_signature.hAlign = 'CENTER'  # Adjust alignment if necessary
        content.append(landlord_signature)
    else:
        content.append(Paragraph("Tenant Signature: ___________________________", styles["Normal"]))
    content.append(Spacer(1, 0.2 * inch))

    if tenant_signature_path and os.path.exists(tenant_signature_path):
        # Add the tenant signature image
        content.append(Paragraph("Tenant Signature:"))
        tenant_signature = Image(tenant_signature_path, width=200, height=50)
        tenant_signature.hAlign = 'CENTER'  # Adjust alignment if necessary
        content.append(tenant_signature)
    else:
        content.append(Paragraph("Tenant Signature: ___________________________", styles["Normal"]))

    # Build PDF
    pdf.build(content)

    # Save lease document path to DB
    lease.document_url = f"lease_{lease_id}.pdf"
    db.session.commit()

    return send_file(file_path, as_attachment=True)

@api.route("/download_lease/<int:user_id>", methods=["GET"])
def download_lease(user_id):
    tenant = Tenant.query.filter_by(user_id=user_id).first()
    print("TENANT: ", tenant)
    if not tenant:
        return jsonify({"message": "Tenant not found"}), 404

    lease = LeaseAgreement.query.filter_by(tenant_id=tenant.id).first()
    if not lease or not lease.document_url:
        return jsonify({"message": "Lease document not found"}), 404

    print('LEASE: ', lease)
    print('LEASE Document_URL: ', lease.document_url)

    # Ensure the lease document path is correctly formed
    lease_folder = os.path.join(current_app.root_path, "leases")  # Assuming leases folder is in the Flask project root
    lease_file_path = os.path.join(lease_folder, lease.document_url)  # lease.document_url stores just the filename

    if not os.path.exists(lease_file_path):
        return jsonify({"message": "Lease file missing"}), 404

    return send_file(lease_file_path, as_attachment=True)