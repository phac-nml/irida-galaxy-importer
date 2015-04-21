#!/bin/bash
rm -rf tests/integration/repos/*
cp ../README.md README.md
tar -cvzf ../irida_export_tool.tar.gz * 
rm README.md
