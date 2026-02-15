from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.customer_profile import CustomerProfileAnalysisRequest, CustomerProfileResponse
from app.services.customer_profile_service import CustomerProfileService

router = APIRouter()


@router.post("/analyze-customer-profile", response_model=CustomerProfileResponse, status_code=status.HTTP_201_CREATED)
async def analyze_customer_profile(
    request: CustomerProfileAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    分析客户画像
    
    - **customer_id**: 客户ID
    - **presale_ticket_id**: 售前工单ID（可选）
    - **communication_notes**: 沟通记录文本
    """
    try:
        service = CustomerProfileService(db)
        profile = await service.analyze_customer(
            customer_id=request.customer_id,
            communication_notes=request.communication_notes,
            presale_ticket_id=request.presale_ticket_id
        )
        return CustomerProfileResponse(**profile.to_dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze customer profile: {str(e)}"
        )


@router.get("/customer-profile/{customer_id}", response_model=CustomerProfileResponse)
async def get_customer_profile(
    customer_id: int,
    db: Session = Depends(get_db)
):
    """
    获取客户画像
    
    - **customer_id**: 客户ID
    """
    service = CustomerProfileService(db)
    profile = service.get_customer_profile(customer_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer profile not found for customer_id: {customer_id}"
        )
    
    return CustomerProfileResponse(**profile.to_dict())
