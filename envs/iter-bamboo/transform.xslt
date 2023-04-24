<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<!--
Cobertura to Clover XML report converter, copied from
https://github.com/cwacek/cobertura-clover-transform

This file is covered by the following licence:

The MIT License (MIT)

Copyright (c) 2014 Chris W

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
-->
    <xsl:output method="xml"/>
<!-- This template processes the root node ("/") -->
<xsl:template match="/">
    <coverage>
        <xsl:attribute name='generated'>
            <xsl:value-of select='/coverage/@timestamp'/>
        </xsl:attribute>
        <project>
            <xsl:attribute name='timestamp'>
                <xsl:value-of select='/coverage/@timestamp'/>
            </xsl:attribute>
        <xsl:apply-templates
            select='//classes'/>
        <xsl:variable name='ncloc' select='count(current()//line)'/>
        <xsl:call-template name='metrics'>
            <xsl:with-param name='ncloc'
                select="$ncloc"
                />
            <xsl:with-param name='files'
                select="count(current()//classes)"
                />
            <xsl:with-param name='elements'
                select='$ncloc'/>
            <xsl:with-param name='coveredelements'
                select='number($ncloc) - count(current()//line[number(@hits) = 0])'/>
        </xsl:call-template>
        </project>
    </coverage>
</xsl:template>
<xsl:template match="class">
    <file>
        <xsl:attribute name='name'>
            <xsl:value-of select='current()/@filename'/>
        </xsl:attribute>
        <xsl:for-each select='lines/line'>
            <line type='stmt'>
                <xsl:attribute name='num'>
                    <xsl:value-of select='current()/@number'/>
                </xsl:attribute>
                <xsl:attribute name='count'>
                    <xsl:value-of select='current()/@hits'/>
                </xsl:attribute>
            </line>
        </xsl:for-each>
        <xsl:variable name='ncloc' select='count(current()//line)'/>
        <xsl:call-template name='metrics'>
            <xsl:with-param name='ncloc'
                select="$ncloc"
                />
            <xsl:with-param name='files'
                select="count(current()//classes)"
                />
            <xsl:with-param name='elements'
                select='$ncloc'/>
            <xsl:with-param name='coveredelements'
                select='number($ncloc) - count(current()//line[number(@hits) = 0])'/>
        </xsl:call-template>
    </file>
</xsl:template>
<xsl:template name='metrics'>
    <xsl:param name='elements' select='number(0)'/>
    <xsl:param name='coveredelements' select='number(0)'/>
    <xsl:param name='files'/>
    <xsl:param name='ncloc' select='number(0)'/>
    <metrics>
        <xsl:attribute name='ncloc'>
            <xsl:value-of select='$ncloc'/>
        </xsl:attribute>
        <xsl:if test='number(coveredelements) != 0'>
            <xsl:attribute name='coveredelements'>
                <xsl:value-of select='$coveredelements'/>
            </xsl:attribute>
        </xsl:if>
        <xsl:if test='number(elements) != 0'>
            <xsl:attribute name='elements'>
                <xsl:value-of select='$elements'/>
            </xsl:attribute>
        </xsl:if>
        <xsl:if test='files != 0'>
            <xsl:attribute name='files'>
                <xsl:value-of select='$files'/>
            </xsl:attribute>
        </xsl:if>
    </metrics>
</xsl:template>
</xsl:stylesheet>
