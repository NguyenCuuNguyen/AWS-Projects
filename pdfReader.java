package com.Apache.PDFBox;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;

public class pdfReader{
	public static void main(String args[]) throws IOException {
		//Loading a PDF Document:
		File file = new File("~/Users/irisnguyen/Documents/My everything 2/Computer Science/ATCS/AsIRemember");
		PDocument document = PDDocument.load(file);
		//Instantiate PDFTextStripper class
		PDFTextStripper pdfStripper = new PDFTextStrippeer();
		//Retrieving text from PDF document
		String text = pdfStripper.getText(document);
		System.out.println(text);
		//Closing the document 
		document.close();
	}

}
