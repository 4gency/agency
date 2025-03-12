#!/usr/bin/env python3
import os
import logging
import colorlog


def setup_logger(name, level=logging.INFO):
    """Configura e retorna um logger colorido."""
    # Criar o logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remover handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Criar um handler para o console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Definir o formato com cores
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(formatter)
    
    # Adicionar o handler ao logger
    logger.addHandler(console_handler)
    
    # Criar um handler para arquivo
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    file_handler = logging.FileHandler(os.path.join(logs_dir, f"{name}.log"))
    file_handler.setLevel(level)
    
    # Definir o formato sem cores para o arquivo
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    
    # Adicionar o handler ao logger
    logger.addHandler(file_handler)
    
    return logger 