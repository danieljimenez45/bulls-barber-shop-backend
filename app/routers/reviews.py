from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewOut

router = APIRouter()


@router.get("/", response_model=List[ReviewOut])
def listar_resenas(
    solo_visibles: bool = True,
    db: Session = Depends(get_db),
):
    query = db.query(Review)
    if solo_visibles:
        query = query.filter(Review.visible == True)  # noqa: E712
    return query.order_by(Review.created_at.desc()).all()


@router.post("/", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def crear_resena(data: ReviewCreate, db: Session = Depends(get_db)):
    review = Review(**data.model_dump())
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.patch("/{review_id}/visibilidad", response_model=ReviewOut)
def cambiar_visibilidad(
    review_id: int, visible: bool, db: Session = Depends(get_db)
):
    """Moderar reseñas (mostrar/ocultar)."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Reseña no encontrada")
    review.visible = visible
    db.commit()
    db.refresh(review)
    return review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_resena(review_id: int, db: Session = Depends(get_db)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Reseña no encontrada")
    db.delete(review)
    db.commit()
