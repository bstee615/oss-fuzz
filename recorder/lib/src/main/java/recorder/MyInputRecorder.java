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

// Wraps the native FuzzedDataProviderImpl and serializes all its return values as JSONL.
public final class MyInputRecorder implements AutoCloseable {
  private Gson gson;
  private Writer writer;
  private Writer resultWriter;
  String lastLocation = null;
  private int ordinal = -1;

  public MyInputRecorder(String baseDir, String fuzzerTargetName) {
    String filename = String.format("%s/fuzzerOutput_%s.jsonl", baseDir, fuzzerTargetName);
    String resultFilename = String.format("%s/fuzzerResult_%s.jsonl", baseDir, fuzzerTargetName);
    try {
        this.writer = new BufferedWriter(new FileWriter(filename, true));
        this.resultWriter = new BufferedWriter(new FileWriter(resultFilename, true));
    }
    catch (IOException ex) {
        System.err.printf("Error initializing writer: %s%n", filename);
    }
    this.gson = new Gson();
  }

  public void close() throws Exception {
    this.writer.close();
    this.resultWriter.close();
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

  public MyInputRecorder setLocation(String location) {
    assert lastLocation == null;
    lastLocation = location;
    return this;
  }

  private String encodeData(String type, String value) {
    // StackTraceElement[] stackTrace = Thread.currentThread().getStackTrace(); // NOTE: disable because no longer needed
    // assert lastLocation != null;
    String result = String.format("{\"type\": \"%s\", \"value\": %s, \"location\": %s}", type, value, lastLocation);
    lastLocation = null;
    return result;
  }

  private String encodeData(String type, int value) {
    return encodeData(type, String.valueOf(value));
  }

  private String encodeData(String type) {
    return encodeData(type, null);
  }
  
  public void markBeginFuzzer() {
    ordinal ++;
    recordTag("begin", ordinal);
  }
  
  public void markEndFuzzer() {
    recordTag("end", ordinal);
  }

  /* BEGIN GENERATED METHODS */
  public void recordTag(String tag, int value) {
    writeToFile(encodeData(tag, gson.toJson(value)));
  }

  public boolean recordAndReturn(boolean object) {
    writeToFile(encodeData("boolean", gson.toJson(object)));
    return object;
  }

  public boolean[] recordAndReturn(boolean[] object) {
    writeToFile(encodeData("boolean[]", gson.toJson(object)));
    return object;
  }

  public byte recordAndReturn(byte object) {
    writeToFile(encodeData("byte", gson.toJson(object)));
    return object;
  }

  public byte[] recordAndReturn(byte[] object) {
    writeToFile(encodeData("byte[]", gson.toJson(object)));
    return object;
  }

  public short recordAndReturn(short object) {
    writeToFile(encodeData("short", gson.toJson(object)));
    return object;
  }

  public short[] recordAndReturn(short[] object) {
    writeToFile(encodeData("short[]", gson.toJson(object)));
    return object;
  }

  public long recordAndReturn(long object) {
    writeToFile(encodeData("long", gson.toJson(object)));
    return object;
  }

  public long[] recordAndReturn(long[] object) {
    writeToFile(encodeData("long[]", gson.toJson(object)));
    return object;
  }

  public int recordAndReturn(int object) {
    writeToFile(encodeData("int", gson.toJson(object)));
    return object;
  }

  public int[] recordAndReturn(int[] object) {
    writeToFile(encodeData("int[]", gson.toJson(object)));
    return object;
  }

  public float recordAndReturn(float object) {
    writeToFile(encodeData("float", gson.toJson(object)));
    return object;
  }

  public float[] recordAndReturn(float[] object) {
    writeToFile(encodeData("float[]", gson.toJson(object)));
    return object;
  }

  public char recordAndReturn(char object) {
    writeToFile(encodeData("char", gson.toJson(object)));
    return object;
  }

  public char[] recordAndReturn(char[] object) {
    writeToFile(encodeData("char[]", gson.toJson(object)));
    return object;
  }

  public double recordAndReturn(double object) {
    writeToFile(encodeData("double", gson.toJson(object)));
    return object;
  }

  public double[] recordAndReturn(double[] object) {
    writeToFile(encodeData("double[]", gson.toJson(object)));
    return object;
  }

  public String recordAndReturn(String object) {
    writeToFile(encodeData("String", gson.toJson(object)));
    return object;
  }

  public int recordAndReturnCount(int object) {
    writeToFile(encodeData("int_count", gson.toJson(object)));
    return object;
  }
  /* END GENERATED METHODS */
}