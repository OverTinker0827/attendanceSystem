"""
Utility functions for the attendance system.
Includes face matching logic, authentication, subnet verification, and data processing.
"""

import numpy as np
from typing import List, Tuple
import base64
import secrets
import ipaddress
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
    a = np.array(vec1)
    b = np.array(vec2)

    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    similarity = dot_product / (norm_a * norm_b)
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
        stored_embeddings: List of stored embeddings for the student
        threshold: Similarity threshold (uses config default if None)
        min_matches: Minimum required matches (uses config default if None)

    Returns:
        Tuple of (is_verified, similarity_scores, num_matches)
    """
    if threshold is None:
        threshold = config.SIMILARITY_THRESHOLD
    if min_matches is None:
        min_matches = config.MIN_MATCHES_REQUIRED

    similarity_scores = []
    for stored_embedding in stored_embeddings:
        score = cosine_similarity(live_embedding, stored_embedding)
        similarity_scores.append(score)

    num_matches = sum(1 for score in similarity_scores if score >= threshold)
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
    if not isinstance(embedding, list):
        return False, "Embedding must be a list"

    if len(embedding) != config.EMBEDDING_DIMENSION:
        return False, f"Embedding dimension must be {config.EMBEDDING_DIMENSION}, got {len(embedding)}"

    try:
        _ = [float(x) for x in embedding]
    except (ValueError, TypeError):
        return False, "All embedding elements must be numbers"

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
    if len(embeddings) != config.NUM_EMBEDDINGS:
        return False, f"Must provide exactly {config.NUM_EMBEDDINGS} embeddings, got {len(embeddings)}"

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
        scheme, credentials = authorization.split()
        if scheme.lower() != "basic":
            return False

        decoded = base64.b64decode(credentials).decode("utf-8")
        username, password = decoded.split(":", 1)

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


def check_subnet_match(client_ip: str, classroom_ip: str, subnet_mask: int = 24) -> bool:
    """
    Check if client IP is in the same subnet as classroom IP.

    Uses proper IP subnet logic (not string matching).
    Default subnet mask is /24 (255.255.255.0)

    Args:
        client_ip: IP address of the client making the request
        classroom_ip: IP address associated with the classroom
        subnet_mask: Subnet mask bits (default: 24 for /24 network)

    Returns:
        True if IPs are in same subnet, False otherwise
    """
    try:
        # Handle localhost/loopback for development
        if client_ip in ["127.0.0.1", "::1", "localhost"]:
            # In development, allow localhost
            # In production, this should be removed or made configurable
            return True

        # Parse IP addresses
        client = ipaddress.ip_address(client_ip)
        classroom = ipaddress.ip_address(classroom_ip)

        # Create network objects with subnet mask
        client_network = ipaddress.ip_network(f"{client_ip}/{subnet_mask}", strict=False)
        classroom_network = ipaddress.ip_network(f"{classroom_ip}/{subnet_mask}", strict=False)

        # Check if both IPs are in the same subnet
        return client_network == classroom_network

    except ValueError as e:
        # Invalid IP address format
        print(f"IP validation error: {e}")
        return False