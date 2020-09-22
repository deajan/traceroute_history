#! /usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
traceroute_history is a quick tool to make traceroute / tracert calls, and store it's results into a database if it
differs from last call.

These are the CRUD operation functions for our data

"""

__intname__ = 'traceroute_history'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__version__ = '0.4.1'
__build__ = '2020092201'


from sqlalchemy.orm import Session
import models
import schemas

def get_target(db: Session, id: int = None, name: str = None):
    if id:
        return db.query(models.Target).filter(models.Target.id == id).first()
    if name:
        return db.query(models.Target).filter(models.Target.name == name).first()


def get_targets(db: Session, skip: int = 0, limit: int = None):
    return db.query(models.Target).offset(skip).limit(limit).all()


def create_target(db: Session, target: schemas.TargetCreate):
    db_target = models.Target(name=target.name, address=target.address, groups=target.groups)
    db.add(db_target)
    db.commit()
    db.refresh(db_target)
    return db_target


def delete_target(db: Session, id: int = None, name: str = None):
    target = get_target(db, id, name)
    if target:
        db.delete(target)
        return db.commit()
    return False


def get_group(db: Session, id: int = None, name: str = None):
    if id:
        return db.query(models.Group).filter(models.Group.id == id).first()
    if name:
        return db.query(models.Group).filter(models.Group.name == name).first()


def get_groups(db: Session, skip: int = 0, limit: int = None):
    return db.query(models.Group).offset(skip).limit(limit).all()


def get_groups_by_target(db: Session, target_id: int = None, target_name: str = None):
    return db.query(models.Group).filter(models.Group.targets.any(id=target_id)).all()


def create_group(db: Session, group: schemas.GroupCreate):
    db_group = models.Group(name=group.name)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group


def delete_group(db: Session, id: int = None, name: str = None):
    group = get_group(db, id, name)
    if group:
        db.delete(group)
        return db.commit(group)
    return False


def get_traceroutes_by_target(db: Session, target_id: int = None, target_name: str = None, skip: int = 0, limit: int = None, count=False):
    target = get_target(db, id=target_id, name=target_name)
    if target:
        if count:
            return db.query(models.Traceroute).filter(models.Traceroute.target == target).count()
        else:
            return db.query(models.Traceroute).filter(models.Traceroute.target == target).order_by(models.Traceroute.id.desc()).limit(limit).offset(skip).all()
    else:
        return None


def get_traceroutes(db: Session, skip: int = 0, limit: int = None):
    return db.query(models.Traceroute).offset(skip).limit(limit).all()


def create_target_traceroute(db: Session, traceroute: schemas.TracerouteCreate, target_id: int):
    db_traceroute = models.Traceroute(**traceroute.dict(), target_id=target_id)
    db.add(db_traceroute)
    db.commit()
    db.refresh(db_traceroute)
    return db_traceroute


def delete_traceroute_by_target(db: Session, target_id: int = None, target_name: str = None):
    target = get_target(db, id=target_id, name=target_name)
    if target:
        traceroutes = get_traceroutes_by_target(db, target_id=target.id)
        for traceroute in traceroutes:
            db.delete(traceroute)
        return db.commit()
    return None
