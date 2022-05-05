#! /usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
traceroute_history is a quick tool to make traceroute / tracert calls, and store it's results into a database if it
differs from last call.

This file contains the pydantic data validation schemas

"""

__intname__ = 'traceroute_history.schemas'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__version__ = '0.4.0'
__build__ = '2020050601'


from pydantic import BaseModel, Field, constr
from typing import List, Optional, Union
from ipaddress import IPv4Address, IPv6Address
import datetime

FQDN = constr(min_length=2, max_length=2083, strip_whitespace=True, regex=r'^(?!:\/\/)(?=.{1,255}$)((.{1,63}\.){1,127}(?![0-9]*$)[a-z0-9-]+\.?)$')


class TracerouteBase(BaseModel):
    raw_traceroute: str = Field(..., description='Raw version of a traceroute', max_length=65535)


class TracerouteCreate(TracerouteBase):
    """
    This model is for creation, since we ignore id an creation date
    """
    pass

class Traceroute(TracerouteBase):
    """
    This model is for reading, since we are supposed to know id an creation date

    """
    id: int
    target_id: int = Field(..., descrption='Owner target id')
    creation_date: datetime.datetime = Field(None, description='Creation date, is set automagically')

    class Config:
        orm_mode = True


class GroupBase(BaseModel):
    name: str = Field(..., description='User friendly group name', max_length=255)


class GroupCreate(GroupBase):
    pass


class Group(GroupBase):
    id: int
    creation_date: datetime.datetime = Field(None, description='Creation date, is set automagically')
    update_date: datetime.datetime = Field(None, description='Record update date, is set automagically')

    class Config:
        orm_mode = True


class TargetBase(BaseModel):
    name: str = Field(..., description='User friendly name target name', max_length=255)
    address: Union[IPv4Address, IPv6Address, FQDN] = Field(..., description='Address should be a IPv4, IPv6 or a fqdn address')
    groups: Optional[List[Group]] = Field(None, description='List of groups as group Schemas')


class TargetCreate(TargetBase):
    groups: Optional[List[GroupCreate]] = Field(None, description='List of groups as group Schemas')


class Target(TargetBase):
    id: int
    creation_date: datetime.datetime = Field(None, description='Creation date, is set automagically')
    update_date: datetime.datetime = Field(None, description='Record update date, is set automagically')

    class Config:
        orm_mode = True
