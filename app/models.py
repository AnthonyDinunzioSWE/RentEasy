from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

db = SQLAlchemy()
migrate = Migrate()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum('Admin', 'Landlord', 'Tenant', name="user_roles"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    landlord_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    properties = db.relationship('Property', backref='landlord', lazy=True)
    tenants = db.relationship(
        'Tenant', 
        backref='landlord', 
        foreign_keys='Tenant.landlord_id'
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat(),  # Convert datetime to string
            'landlord_id': self.landlord_id
        }


class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    landlord_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    unit_number = db.Column(db.String(20), nullable=True)
    rent_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default="Available")

    tenants = db.relationship('Tenant', backref='property', lazy=True)
    lease_agreements = db.relationship('LeaseAgreement', backref='property', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'landlord_id': self.landlord_id,
            'address': self.address,
            'unit_number': self.unit_number,
            'rent_amount': self.rent_amount,
            'status': self.status
        }


class Tenant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    tenant_name = db.Column(db.String(250))
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    property_address = db.Column(db.String(500))
    landlord_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    landlord_name = db.Column(db.String(250))
    lease_start = db.Column(db.DateTime, nullable=False)
    lease_end = db.Column(db.DateTime, nullable=False)
    signed_status = db.Column(db.Boolean, default=False)

    invoices = db.relationship('Invoice', backref='tenant', lazy=True)
    lease_agreements = db.relationship('LeaseAgreement', backref='tenant', lazy=True)
    payments = db.relationship('Payment', backref='tenant', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'tenant_name': self.tenant_name,
            'property_id': self.property_id,
            'property_address': self.property_address,
            'landlord_id': self.landlord_id,
            'landlord_name': self.landlord_name,
            'lease_start': self.lease_start.isoformat(),
            'lease_end': self.lease_end.isoformat(),
            'signed_status': self.signed_status
        }


class LeaseAgreement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    landlord_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    document_url = db.Column(db.String(500))
    signed_status = db.Column(db.Boolean, default=False)
    lease_start = db.Column(db.DateTime, nullable=False)
    lease_end = db.Column(db.DateTime, nullable=False)
    tenant_name = db.Column(db.String(250))
    property_name = db.Column(db.String(250))
    rent = db.Column(db.Float)
    tenant_signature_path = db.Column(db.String(500))
    landlord_signature_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'property_id': self.property_id,
            'tenant_id': self.tenant_id,
            'landlord_id': self.landlord_id,
            'document_url': self.document_url,
            'signed_status': self.signed_status,
            'lease_start': self.lease_start.isoformat(),
            'lease_end': self.lease_end.isoformat(),
            'tenant_name': self.tenant_name,
            'property_name': self.property_name,
            'rent': self.rent,
            'tenant_signature_path': self.tenant_signature_path,
            'landlord_signature_path': self.landlord_signature_path,
            'created_at': self.created_at.isoformat()
        }


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    landlord_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    paid_amount = db.Column(db.Float, nullable=False, default=0.0)
    description = db.Column(db.String(500))
    tenant_name = db.Column(db.String(255))
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    payments = db.relationship('Payment', backref='invoice', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'landlord_id': self.landlord_id,
            'amount': self.amount,
            'paid_amount': self.paid_amount,
            'description': self.description,
            'tenant_name': self.tenant_name,
            'due_date': self.due_date.isoformat(),
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'tenant_id': self.tenant_id,
            'amount_paid': self.amount_paid,
            'payment_date': self.payment_date.isoformat()
        }
