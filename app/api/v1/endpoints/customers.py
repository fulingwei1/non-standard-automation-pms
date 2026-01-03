from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api import deps
from app.models.project import Customer
from app.schemas.project import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
)

router = APIRouter()


@router.get("/", response_model=List[CustomerResponse])
def read_customers(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 20,
    name: str = Query(None, description="Filter by customer name"),
) -> Any:
    """
    Retrieve customers.
    """
    query = db.query(Customer)
    if name:
        query = query.filter(Customer.customer_name.contains(name))
    customers = (
        query.order_by(desc(Customer.created_at)).offset(skip).limit(limit).all()
    )
    return customers


@router.post("/", response_model=CustomerResponse)
def create_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_in: CustomerCreate,
) -> Any:
    """
    Create new customer.
    """
    customer = (
        db.query(Customer)
        .filter(Customer.customer_code == customer_in.customer_code)
        .first()
    )
    if customer:
        raise HTTPException(
            status_code=400,
            detail="The customer with this code already exists in the system.",
        )

    customer = Customer(**customer_in.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerResponse)
def read_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: int,
) -> Any:
    """
    Get customer by ID.
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: int,
    customer_in: CustomerUpdate,
) -> Any:
    """
    Update a customer.
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    update_data = customer_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}", response_model=CustomerResponse)
def delete_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: int,
) -> Any:
    """
    Delete a customer (soft delete ideally, but here hard delete or active flag).
    Let's use hard delete for now or check requirements.
    Models usually have is_active.
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Check if used in projects
    if customer.projects:
        raise HTTPException(
            status_code=400, detail="Cannot delete customer with associated projects"
        )

    db.delete(customer)
    db.commit()
    return customer
