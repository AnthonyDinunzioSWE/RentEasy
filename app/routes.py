from io import BytesIO
import os
from flask import Blueprint, current_app, jsonify, render_template, redirect, url_for, request, session, flash, send_file
from .models import db, User, Tenant, Property, Payment, Invoice, LeaseAgreement
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from PIL import *
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from werkzeug.utils import secure_filename
import base64



main = Blueprint('main', __name__)


@main.route('/')
def home():
    return render_template('index.html')

@main.route('/delete_all_tenants')
def delete_all_tenants():
    users = User.query.filter_by(role="Tenant").all()
    tenants = Tenant.query.all()

    for user in users:
        db.session.delete(user)
        db.session.commit()
    for tenant in tenants:
        db.session.delete(tenant)
        db.session.commit()
    
    db.session.commit()
    return jsonify({'message': "SUCCESSFULLY DELETED ALL TENANTS!"})

@main.route('/get_lease_by_tenant/<int:tenant_id>')
def get_lease_by_tentant(tenant_id):
    tenant = Tenant.query.get(tenant_id)
    lease = 'Searching For Lease'
    print(f'CURRENT TENANT: {tenant}')
    print(f'CURRENT TENANT ID: {tenant.id}')
    if tenant:
        lease = LeaseAgreement.query.filter_by(tenant_id=tenant.id).first()
        print(f'Lease: {lease}')
        print(f'Lease Data: {lease}')
    return jsonify({'data': "TESTING"})

@main.route('/delete_user/<email>')
def delete_user(email):
    user = User.query.filter_by(email=email).first()
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': f'Successfully Deleted User: {user.email}'})
    else:
        return jsonify({'message': 'Failed To Delete User'})

@main.route('/create_admin')
def create_admin():
    new_user = User(name="Anthony Dinunzio", email='anthonydinunziopr@gmail.com', password_hash=generate_password_hash('5199152396aA!'), role='Admin')
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'ADMIN USER SUCCESSFULLY CREATED'})

@main.route('/create_landlord')
def create_landlord():
    new_user = User(name="Anthony Dinunzio", email='anthonydinunzio@gmail.com', password_hash=generate_password_hash('5199152396aA!'), role='Landlord')
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Landlord USER SUCCESSFULLY CREATED'})

@main.route('/pricing')
def pricing():
    return render_template('pricing.html')

@main.route('/faq')
def faq():
    return render_template('faq.html')

@main.route('/get_all_user_data')
def get_users_data():
    users = User.query.all()  # Get all users
    users_lst = []
    tenants = []
    tenant_ids = []

    for user in users:
        tenant_list = Tenant.query.filter_by(user_id=user.id).all()  # Execute the query and get the tenants list
        tenants.extend(tenant_list)  # Add tenants to the list
        
        # Add tenant IDs to the list
        tenant_ids.extend([tenant.id for tenant in tenant_list])

        users_lst.append(user)

    # Now, fetch all leases with the tenant_ids
    leases = LeaseAgreement.query.filter(LeaseAgreement.tenant_id.in_(tenant_ids)).all()

    return jsonify({'users': [user.to_dict() for user in users_lst], 'tenants': [tenant.to_dict() for tenant in tenants], 'leases': [lease.to_dict() for lease in leases]})



@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email and password:
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                session['user_id'] = user.id
                session['user_role'] = user.role
                if user.role == 'Admin':
                    return redirect(url_for('main.dashboard'))
                if user.role == 'Landlord':
                    return redirect(url_for('main.tenants'))
    return render_template('login.html')
            

@main.route('/dashboard')
def dashboard():
    user = User.query.get(session['user_id'])
    if user and user.role == 'Admin':
        users = User.query.all()
        tenants = Tenant.query.all()
        properties = Property.query.all()
        payments = Payment.query.all()
        invoices = Invoice.query.all()
        lease_agreements = LeaseAgreement.query.all()
        return render_template('dashboard.html', users=users, tenants=tenants, properties=properties, payments=payments,
                               invoices=invoices, lease_agreements=lease_agreements)


@main.route('/properties', methods=['GET', 'POST'])
def properties():
    user = User.query.get(session['user_id'])
    if user.role != 'Landlord':
        flash("Access denied.", "danger")
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        # Handle new property creation
        address = request.form.get('address')
        unit_number = request.form.get('unit_number')
        rent_amount = request.form.get('rent_amount')
        status = request.form.get('status')

        new_property = Property(
            landlord_id=user.id, 
            address=address, 
            unit_number=unit_number, 
            rent_amount=rent_amount, 
            status=status
        )
        db.session.add(new_property)
        db.session.commit()
        flash("Property added successfully!", "success")
        return redirect(url_for('main.properties'))

    properties = Property.query.filter_by(landlord_id=user.id).all()
    return render_template('properties.html', properties=properties)

@main.route('/add_property', methods=["GET", "POST"])
def add_property():
    user_id = session['user_id']
    user = User.query.get(user_id)
    if user:
        if user.role == "Landlord":
            if request.method == "POST":
                address = request.form.get('address')
                unit_number = request.form.get('unit_number')
                rent_amount = request.form.get('rent_amount')
                status = request.form.get('status')

                new_property = Property(
                    landlord_id=user.id, 
                    address=address, 
                    unit_number=unit_number, 
                    rent_amount=rent_amount, 
                    status=status
                )
                db.session.add(new_property)
                db.session.commit()
                flash("Property added successfully!", "success")
                return redirect(url_for('main.properties'))
            return render_template('add_property.html')

@main.route('/update_property', methods=['POST'])
def update_property():
    user = User.query.get(session['user_id'])
    if user.role != 'Landlord':
        flash("Access denied.", "danger")
        return redirect(url_for('main.home'))

    if request.method == 'POST' and '_method' in request.form and request.form['_method'] == 'PATCH':
        property_id = request.form.get('property_id')
        prop = Property.query.get(property_id)

        if prop and prop.landlord_id == user.id:
            prop.address = request.form.get('address', prop.address)
            prop.unit_number = request.form.get('unit_number', prop.unit_number)
            prop.rent_amount = request.form.get('rent_amount', prop.rent_amount)
            prop.status = request.form.get('status', prop.status)

            db.session.commit()
            flash("Property updated successfully!", "success")
        else:
            flash("Property not found or access denied.", "danger")
        
        return redirect(url_for('main.properties'))
    
@main.route('/delete_property/<int:property_id>', methods=['POST'])
def delete_property(property_id):
    property_to_delete = Property.query.get(property_id)
    if property_to_delete:
        db.session.delete(property_to_delete)
        db.session.commit()
    return redirect(url_for('main.properties'))  # Or another page

@main.route('/tenants', methods=['GET', 'POST'])
def tenants():
    user = User.query.get(session['user_id'])
    if user.role != 'Landlord':
        flash("Access denied.", "danger")
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        property_id = request.form.get('property_id')  # Get the selected property ID from the form
        lease_start_str = request.form.get('lease_start')
        lease_end_str = request.form.get('lease_end')

        lease_start = datetime.strptime(lease_start_str, '%Y-%m-%d')
        lease_end = datetime.strptime(lease_end_str, '%Y-%m-%d')

        new_user = User(name=name, email=email, password_hash=generate_password_hash(password), role='Tenant', landlord_id=session['user_id'])
        db.session.add(new_user)
        db.session.commit() 
        
        tenant_user = User.query.get(new_user.id)
        tenant_user_name = tenant_user.name

        tenant_property = Property.query.get(property_id)
        tenant_property_address = tenant_property.address

        tenant_landlord = User.query.get(session['user_id'])
        tenant_landlord_name = tenant_landlord.name

        new_tenant = Tenant(user_id=new_user.id, landlord_id=session['user_id'], property_id=property_id, lease_start=lease_start, lease_end=lease_end, tenant_name=tenant_user_name, property_address=tenant_property_address, landlord_name=tenant_landlord_name)
        db.session.add(new_tenant)
        db.session.commit()

        flash("Tenant added successfully!", "success")
        return redirect(url_for('main.tenants'))
    
    # Query the user's properties
    properties = Property.query.filter_by(landlord_id=session['user_id']).all()
    tenant_users = User.query.filter_by(role='Tenant', landlord_id=session['user_id']).all()
    tenants = Tenant.query.filter_by(landlord_id=user.id).all()
    return render_template('tenants.html', tenants=tenants, properties=properties, tenant_users=tenant_users)

@main.route('/update_tenant', methods=['POST'])
def update_tenant():
    tenant_id = request.form.get('tenant_id')
    tenant = Tenant.query.get(tenant_id)

    if tenant:
        tenant_user = User.query.get(tenant.user_id)
        tenant_user.name = request.form.get('name')
        tenant_user.email = request.form.get('email')
        lease_start_str = request.form.get('lease_start')
        lease_end_str = request.form.get('lease_end')
        tenant.lease_start = datetime.strptime(lease_start_str, '%Y-%m-%d')
        tenant.lease_end = datetime.strptime(lease_end_str, '%Y-%m-%d')



        db.session.commit()
        flash("Tenant updated successfully!", "success")

    return redirect(url_for('main.tenants'))

@main.route('/delete_tenant/<int:user_id>', methods=['POST'])
def delete_tenant(user_id):
    tenant_user = User.query.get(user_id)
    tenant = Tenant.query.filter_by(user_id=user_id)

    if tenant_user and tenant:
        db.session.delete(tenant)
        db.session.delete(tenant_user)
        db.session.commit()
        flash("Tenant deleted successfully!", "success")
    return redirect(url_for('main.tenants'))

@main.route('/leases', methods=['GET', 'POST'])
def leases():
    user = User.query.get(session['user_id'])
    
    if user.role != 'Landlord':
        flash("Access denied.", "danger")
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        tenant_id = request.form.get('tenant_id')
        property_id = request.form.get('property_id')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        rent = request.form.get('rent')

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        tenant_user = User.query.get(tenant_id)
        tenant = Tenant.query.filter_by(user_id=tenant_user.id).first_or_404()
        tenant_name = tenant_user.name
        prop = Property.query.get(property_id)
        property_name = prop.address

        new_lease = LeaseAgreement(
            tenant_id=tenant.id,
            landlord_id=session['user_id'],
            property_id=property_id,
            lease_start=start_date,
            lease_end=end_date,
            tenant_name=tenant_name,
            property_name=property_name,
            rent=rent
        )
        
        db.session.add(new_lease)
        db.session.commit()
        flash("Lease added successfully!", "success")
        return redirect(url_for('main.leases'))

    # Fetch tenants & properties owned by the landlord
    tenants = User.query.filter_by(role='Tenant', landlord_id=user.id).all()
    properties = Property.query.filter_by(landlord_id=user.id).all()
    leases = LeaseAgreement.query.filter_by(landlord_id=user.id).all()

    return render_template('leases.html', tenants=tenants, properties=properties, leases=leases)

@main.route('/check_lease/<int:tenant_id>')
def check_lease(tenant_id):
    tenant = Tenant.query.get_or_404(tenant_id)
    today = datetime.today().date()

    if tenant.lease_end and tenant.lease_end < today:
        flash('error', 'Expired Lease')
        return jsonify({"status": "expired"})
    
    lease = LeaseAgreement.query.filter_by(tenant_id=tenant_id).first()
    if lease:
        flash('success', 'Active Lease')
        return jsonify({"status": "active", "lease_url": url_for('main.download_lease', lease_id=lease.id)})
    
    return jsonify({"status": "no_lease"})

@main.route('/generate_lease/<int:lease_id>')
def generate_lease(lease_id, landlord_signature_path=None, tenant_signature_path=None):
    lease = LeaseAgreement.query.get_or_404(lease_id)
    print('LEASE', lease)
    landlord = User.query.get(lease.landlord_id)
    lease_folder = os.path.join(current_app.root_path, "leases")
    if not os.path.exists(lease_folder):
        os.makedirs(lease_folder)

    file_path = os.path.join(lease_folder, f"lease_{lease_id}.pdf")
    uploads_folder = os.path.join(current_app.root_path, 'uploads')

    print(f"Uploads Folder {uploads_folder}")


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

    landlord_signature_path = os.path.join(lease_folder, lease.landlord_signature_path)
    tenant_signature_path = os.path.join(lease_folder, lease.tenant_signature_path)

    print(f'Landlord sig: {landlord_signature_path}')
    print(f'tenant sig: {tenant_signature_path}')

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
    
    if landlord_signature_path and os.path.exists(landlord_signature_path):
        landlord_signature = Image(landlord_signature_path, width=200, height=50)
        landlord_signature.hAlign = 'CENTER'
        content.append(Paragraph("Landlord Signature:"))
        content.append(landlord_signature)
    else:
        content.append(Paragraph("Landlord Signature: Image not available.", styles["Normal"]))
    if tenant_signature_path:
        print(f"PREV TENANT_SIG_PATH: {tenant_signature_path}")
        # Ensure the tenant signature image exists
        tenant_signature_path = os.path.join(uploads_folder, tenant_signature_path)
        print(f"NEXT TENANT_SIG_PATH: {tenant_signature_path}")
        if os.path.exists(tenant_signature_path):
            tenant_signature = Image(tenant_signature_path, width=200, height=50)
            tenant_signature.hAlign = 'CENTER'
            print(f"TENANT_SIG_IMAGE: {tenant_signature}")
            content.append(Spacer(1, 0.3 * inch))
            content.append(Paragraph("Tenant Signature:"))
            content.append(tenant_signature)
        else:
            content.append(Paragraph("Tenant Signature: Image not available.", styles["Normal"]))
    else:
        content.append(Paragraph("Tenant Signature: ___________________________", styles["Normal"]))

    # Build the PDF
    pdf.build(content)

    return send_file(file_path, as_attachment=True)

@main.route('/leases/sign_lease/<int:lease_id>', methods=['GET', 'POST'])
def sign_lease(lease_id):
    lease = LeaseAgreement.query.get_or_404(lease_id)
    user = User.query.get(session['user_id'])

    if user.role != 'Landlord':
        flash("Access denied.", "danger")
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        signature_data = request.form.get('signatureData')  # Ensure this matches the name in your form

        # Check if signature data exists
        if signature_data:
            print(f"SIGNATURE DATA: {signature_data}")
            try:
                # Remove the base64 prefix (data:image/png;base64,)
                signature_data = signature_data.split(',')[1]
                signature_image = Image.open(BytesIO(base64.b64decode(signature_data)))  # Decode the base64 string

                # Set file path for the image
                lease_folder = os.path.join(current_app.root_path, "leases")
                if not os.path.exists(lease_folder):
                    os.makedirs(lease_folder)

                signature_filename = f"{user.id}_signature.png"
                signature_path = os.path.join(lease_folder, secure_filename(signature_filename))

                # Save the signature image
                signature_image.save(signature_path)
                print(f"IMAGE SAVED: {signature_image}")

                # Update the lease agreement with the signature path
                lease.landlord_signature_path = signature_path
                db.session.commit()

                flash("Lease signed successfully!", "success")
                return redirect(url_for('main.leases'))

            except Exception as e:
                flash(f"Error saving signature: {str(e)}", "danger")
                return redirect(url_for('main.leases'))

        flash("Lease was not signed! Please try again.", "danger")
        return redirect(url_for('main.leases'))

    return render_template('sign_lease.html', lease=lease)

# You can now add the signature canvas to the HTML page where landlords sign the lease.

@main.route('/download_lease/<int:lease_id>')
def download_lease(lease_id):
    lease = LeaseAgreement.query.get_or_404(lease_id)
    generate_lease(lease.id)
    lease_file_path = os.path.join(os.getcwd(), "app", "leases", lease.document_url)

    if not os.path.exists(lease_file_path):
        flash("Lease file not found.", "danger")
        return redirect(url_for('main.leases'))

    return send_file(lease_file_path, as_attachment=True)

@main.route('/update_lease', methods=['POST'])
def update_lease():
    lease_id = request.form.get('lease_id')
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    rent = request.form.get('rent')

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

    lease = LeaseAgreement.query.get(lease_id)
    if lease:
        lease.lease_start = start_date
        lease.lease_end = end_date
        lease.rent = rent
        db.session.commit()
    
    return redirect(url_for('main.leases'))

@main.route('/delete_lease/<int:lease_id>', methods=['POST'])
def delete_lease(lease_id):
    lease = LeaseAgreement.query.get(lease_id)
    if lease:
        db.session.delete(lease)
        db.session.commit()
        flash("Lease deleted successfully!", "success")
    else:
        flash("Lease not found!", "danger")
    
    return redirect(url_for('main.leases'))

@main.route('/billing', methods=['GET', 'POST'])
def billing():
    user = User.query.get(session['user_id'])
    
    if user.role != 'Landlord':
        flash("Access denied.", "danger")
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        tenant_id = request.form.get('tenant_id')
        amount = float(request.form.get('amount'))
        due_date_str = request.form.get('due_date')
        description = request.form.get('description')
        
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        tenant = User.query.get(tenant_id)

        new_invoice = Invoice(
            landlord_id=user.id,
            tenant_id=tenant_id,
            tenant_name=tenant.name,
            amount=amount,
            paid_amount=0.0,
            due_date=due_date,
            description=description,
            status="Pending"
        )
        
        db.session.add(new_invoice)
        db.session.commit()
        flash("Invoice created successfully!", "success")
        return redirect(url_for('main.billing'))
    
    # Fetch invoices, tenants
    invoices = Invoice.query.filter_by(landlord_id=user.id).all()
    tenants = User.query.filter_by(role='Tenant', landlord_id=user.id).all()
    
    return render_template('billing.html', invoices=invoices, tenants=tenants)

@main.route('/update_invoice', methods=['POST'])
def update_invoice():
    invoice_id = request.form.get('invoice_id')
    paid_amount = float(request.form.get('paid_amount'))
    
    invoice = Invoice.query.get(invoice_id)
    if invoice:
        invoice.paid_amount = paid_amount
        if paid_amount >= invoice.amount:
            invoice.status = "Paid"
        elif 0 < paid_amount < invoice.amount:
            invoice.status = "Partially Paid"
        else:
            invoice.status = "Pending"
        db.session.commit()
    
    return redirect(url_for('main.billing'))

@main.route('/delete_invoice/<int:invoice_id>', methods=['POST'])
def delete_invoice(invoice_id):
    invoice = Invoice.query.get(invoice_id)
    if invoice:
        db.session.delete(invoice)
        db.session.commit()
        flash("Invoice deleted successfully!", "success")
    else:
        flash("Invoice not found!", "danger")
    
    return redirect(url_for('main.billing'))

@main.route('/logout')
def logout():
    session['user_id'] = None
    session['user_role'] = None
    return redirect(url_for('main.home'))
