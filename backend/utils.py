"""
Utility functions for the attendance system.
Includes face matching logic, authentication, and data processing.
"""

import numpy as np
from typing import List, Tuple
import base64
import secrets
from config import config


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First embedding vector
        vec2: Second embedding vector
    
    Returns:
        Cosine similarity score (0 to 1, where 1 is identical)
    """
    # Convert to numpy arrays
    a = np.array(vec1)
    b = np.array(vec2)
    
    # Calculate cosine similarity
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    # Avoid division by zero
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    similarity = dot_product / (norm_a * norm_b)
    
    # Clamp to [0, 1] range (should already be in this range for normalized embeddings)
    return float(np.clip(similarity, 0.0, 1.0))


def verify_face(
    live_embedding: List[float],
    stored_embeddings: List[List[float]],
    threshold: float = None,
    min_matches: int = None
) -> Tuple[bool, List[float], int]:
    """
    Verify a live face embedding against stored embeddings.
    
    Args:
        live_embedding: The embedding from the live capture
        stored_embeddings: List of 5 stored embeddings for the student
        threshold: Similarity threshold (uses config default if None)
        min_matches: Minimum required matches (uses config default if None)
    
    Returns:
        Tuple of (is_verified, similarity_scores, num_matches)
    """
    if threshold is None:
        threshold = config.SIMILARITY_THRESHOLD
    
    if min_matches is None:
        min_matches = config.MIN_MATCHES_REQUIRED
    
    # Calculate similarity scores for all stored embeddings
    similarity_scores = []
    for stored_embedding in stored_embeddings:
        score = cosine_similarity(live_embedding, stored_embedding)
        similarity_scores.append(score)
    
    # Count how many scores exceed the threshold
    num_matches = sum(1 for score in similarity_scores if score >= threshold)
    
    # Verify if we have enough matches
    is_verified = num_matches >= min_matches
    
    return is_verified, similarity_scores, num_matches


def validate_embedding(embedding: List[float]) -> Tuple[bool, str]:
    """
    Validate an embedding vector.
    
    Args:
        embedding: The embedding vector to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if embedding is a list
    if not isinstance(embedding, list):
        return False, "Embedding must be a list"
    
    # Check dimension
    if len(embedding) != config.EMBEDDING_DIMENSION:
        return False, f"Embedding dimension must be {config.EMBEDDING_DIMENSION}, got {len(embedding)}"
    
    # Check if all elements are numbers
    try:
        _ = [float(x) for x in embedding]
    except (ValueError, TypeError):
        return False, "All embedding elements must be numbers"
    
    # Check for NaN or infinity
    arr = np.array(embedding)
    if np.isnan(arr).any() or np.isinf(arr).any():
        return False, "Embedding contains NaN or infinity values"
    
    return True, ""


def validate_embeddings_list(embeddings: List[List[float]]) -> Tuple[bool, str]:
    """
    Validate a list of embeddings (for registration).
    
    Args:
        embeddings: List of embedding vectors
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check number of embeddings
    if len(embeddings) != config.NUM_EMBEDDINGS:
        return False, f"Must provide exactly {config.NUM_EMBEDDINGS} embeddings, got {len(embeddings)}"
    
    # Validate each embedding
    for i, embedding in enumerate(embeddings):
        is_valid, error_msg = validate_embedding(embedding)
        if not is_valid:
            return False, f"Embedding {i+1}: {error_msg}"
    
    return True, ""


def verify_basic_auth(authorization: str) -> bool:
    """
    Verify HTTP Basic Authentication credentials.
    
    Args:
        authorization: The Authorization header value (e.g., "Basic base64string")
    
    Returns:
        True if credentials are valid, False otherwise
    """
    if not authorization:
        return False
    
    try:
        # Parse "Basic <credentials>"
        scheme, credentials = authorization.split()
        if scheme.lower() != "basic":
            return False
        
        # Decode base64 credentials
        decoded = base64.b64decode(credentials).decode("utf-8")
        username, password = decoded.split(":", 1)
        
        # Compare with configured credentials
        # Use secrets.compare_digest to prevent timing attacks
        username_match = secrets.compare_digest(username, config.ADMIN_USERNAME)
        password_match = secrets.compare_digest(password, config.ADMIN_PASSWORD)
        
        return username_match and password_match
    
    except Exception:
        return False


def format_similarity_scores(scores: List[float]) -> List[float]:
    """
    Format similarity scores for JSON response (round to 2 decimal places).
    
    Args:
        scores: List of similarity scores
    
    Returns:
        List of rounded scores
    """
    return [round(score, 2) for score in scores]
