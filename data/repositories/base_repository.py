"""
Base repository class for database operations.
"""
from typing import TypeVar, Generic, Optional, List, Type
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from data.db import get_db

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Base repository class for database operations."""
    
    def __init__(self, model_class: Type[T]):
        """
        Initialize repository with model class.
        
        Args:
            model_class: SQLAlchemy model class
        """
        self.model_class = model_class
        self._db: Optional[Session] = None
    
    @property
    def db(self) -> Session:
        """Get database session."""
        if self._db is None:
            self._db = get_db()
        return self._db
    
    def close(self):
        """Close database session."""
        if self._db:
            self._db.close()
            self._db = None
    
    def create(self, **kwargs) -> Optional[T]:
        """
        Create a new record.
        
        Args:
            **kwargs: Model attributes
            
        Returns:
            Created instance or None if error
        """
        try:
            instance = self.model_class(**kwargs)
            self.db.add(instance)
            self.db.commit()
            self.db.refresh(instance)
            return instance
        except SQLAlchemyError as e:
            print(f"Error creating {self.model_class.__name__}: {e}")
            self.db.rollback()
            return None
        except Exception as e:
            print(f"Unexpected error creating {self.model_class.__name__}: {e}")
            self.db.rollback()
            return None
    
    def get_by_id(self, id: int) -> Optional[T]:
        """
        Get record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            Instance or None if not found
        """
        try:
            return self.db.query(self.model_class).filter_by(id=id).first()
        except Exception as e:
            print(f"Error getting {self.model_class.__name__} by id: {e}")
            return None
    
    def get_all(self) -> List[T]:
        """
        Get all records.
        
        Returns:
            List of instances
        """
        try:
            return self.db.query(self.model_class).all()
        except Exception as e:
            print(f"Error getting all {self.model_class.__name__}: {e}")
            return []
    
    def update(self, instance: T) -> Optional[T]:
        """
        Update a record.
        
        Args:
            instance: Instance to update
            
        Returns:
            Updated instance or None if error
        """
        try:
            self.db.commit()
            self.db.refresh(instance)
            return instance
        except SQLAlchemyError as e:
            print(f"Error updating {self.model_class.__name__}: {e}")
            self.db.rollback()
            return None
        except Exception as e:
            print(f"Unexpected error updating {self.model_class.__name__}: {e}")
            self.db.rollback()
            return None
    
    def delete(self, instance: T) -> bool:
        """
        Delete a record.
        
        Args:
            instance: Instance to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.db.delete(instance)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            print(f"Error deleting {self.model_class.__name__}: {e}")
            self.db.rollback()
            return False
        except Exception as e:
            print(f"Unexpected error deleting {self.model_class.__name__}: {e}")
            self.db.rollback()
            return False

