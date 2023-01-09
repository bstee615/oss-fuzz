package recorder;

import com.code_intelligence.jazzer.api.FuzzedDataProvider;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectOutputStream;
import java.io.Writer;
import java.io.BufferedWriter;
import java.io.FileWriter;
import java.util.Set;
import java.util.HashSet;
import java.util.Base64;
import java.lang.AutoCloseable;
import java.lang.Thread;
import java.lang.StackTraceElement;
import com.google.gson.Gson;


// Manages logging the results of the harness to a file.
public final class MyResultRecorder implements AutoCloseable {
  private Gson gson;
  private Writer writer;
  

  public MyResultRecorder(String baseDir, String fuzzerTargetName) {
    String filename = String.format("%s/fuzzerResult_%s.jsonl", baseDir, fuzzerTargetName);
    try {
        this.writer = new BufferedWriter(new FileWriter(filename, true));
    }
    catch (IOException ex) {
        System.err.printf("Error initializing writer: %s%n", filename);
    }
    this.gson = new Gson();
  }

  private void writeToFile(String string) {
    System.err.println(String.format("WRITE TO FILE: \"%s\"", string));
    try {
        this.writer.append(string + "\n");
    }
    catch (IOException ex) {
        System.err.printf("Error writing to file: %s%n", string);
    }
  }

  private void logResultHelper(String value, String location, String type) {
    writeToFile(String.format("{\"value\": %s, \"location\": %s, \"type\": %s}", value, location, gson.toJson(type)));
  }

  public <T> void logResult(T obj, String location) {
    logResultHelper(gson.toJson(obj.toString()), location, "Object");
  }

  public <T> void logResult(boolean obj, String location) {
    logResultHelper(gson.toJson(obj), location, "boolean");
  }

  public <T> void logResult(boolean[] obj, String location) {
    logResultHelper(gson.toJson(obj), location, "boolean[]");
  }

  public <T> void logResult(byte obj, String location) {
    logResultHelper(gson.toJson(obj), location, "byte");
  }

  public <T> void logResult(byte[] obj, String location) {
    logResultHelper(gson.toJson(obj), location, "byte[]");
  }

  public <T> void logResult(char obj, String location) {
    logResultHelper(gson.toJson(obj), location, "char");
  }

  public <T> void logResult(char[] obj, String location) {
    logResultHelper(gson.toJson(obj), location, "char[]");
  }

  public <T> void logResult(int obj, String location) {
    logResultHelper(gson.toJson(obj), location, "int");
  }

  public <T> void logResult(int[] obj, String location) {
    logResultHelper(gson.toJson(obj), location, "int[]");
  }

  public <T> void logResult(short obj, String location) {
    logResultHelper(gson.toJson(obj), location, "short");
  }

  public <T> void logResult(short[] obj, String location) {
    logResultHelper(gson.toJson(obj), location, "short[]");
  }

  public <T> void logResult(float obj, String location) {
    logResultHelper(gson.toJson(obj), location, "float");
  }

  public <T> void logResult(float[] obj, String location) {
    logResultHelper(gson.toJson(obj), location, "float[]");
  }

  public <T> void logResult(double obj, String location) {
    logResultHelper(gson.toJson(obj), location, "double");
  }

  public <T> void logResult(double[] obj, String location) {
    logResultHelper(gson.toJson(obj), location, "double[]");
  }

  public void close() throws Exception {
    this.writer.close();
  }
}