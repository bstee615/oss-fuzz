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

// Serializes fuzzer outputs and harness results as JSONL.
public final class FuzzerRecorder implements AutoCloseable {
  private Gson gson;
  private Writer writer;
  String lastLocation = null;
  private static int ordinal = -1;

  public FuzzerRecorder(String baseDir, String fuzzerTargetName) {
    String filename = String.format("%s/fuzzerOutput_%s.jsonl", baseDir, fuzzerTargetName);
    try {
        this.writer = new BufferedWriter(new FileWriter(filename, true));
    }
    catch (IOException ex) {
        System.err.printf("Error initializing writer: %s%n", filename);
    }
    this.gson = new Gson();
  }

  public void close() throws Exception {
    this.writer.close();
  }

  public FuzzerRecorder setLocation(String location) {
    assert lastLocation == null;
    lastLocation = location;
    return this;
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

  public void markBeginFuzzer() {
    ordinal ++;
    recordTag("begin", ordinal);
  }
  
  public void markEndFuzzer() {
    recordTag("end", ordinal);
  }

  /* BEGIN INPUT METHODS */
  private void logInputHelper(String type, String value) {
    writeToFile(String.format("{\"log_type\": \"input\", \"type\": %s, \"value\": %s, \"location\": %s}", gson.toJson(type), value, lastLocation));
    lastLocation = null;
  }

  public void recordTag(String tag, int value) {
    logInputHelper(tag, gson.toJson(value));
  }

  public boolean recordAndReturn(boolean object) {
    logInputHelper("boolean", gson.toJson(object));
    return object;
  }

  public boolean[] recordAndReturn(boolean[] object) {
    logInputHelper("boolean[]", gson.toJson(object));
    return object;
  }

  public byte recordAndReturn(byte object) {
    logInputHelper("byte", gson.toJson(object));
    return object;
  }

  public byte[] recordAndReturn(byte[] object) {
    logInputHelper("byte[]", gson.toJson(object));
    return object;
  }

  public short recordAndReturn(short object) {
    logInputHelper("short", gson.toJson(object));
    return object;
  }

  public short[] recordAndReturn(short[] object) {
    logInputHelper("short[]", gson.toJson(object));
    return object;
  }

  public long recordAndReturn(long object) {
    logInputHelper("long", gson.toJson(object));
    return object;
  }

  public long[] recordAndReturn(long[] object) {
    logInputHelper("long[]", gson.toJson(object));
    return object;
  }

  public int recordAndReturn(int object) {
    logInputHelper("int", gson.toJson(object));
    return object;
  }

  public int[] recordAndReturn(int[] object) {
    logInputHelper("int[]", gson.toJson(object));
    return object;
  }

  public float recordAndReturn(float object) {
    logInputHelper("float", gson.toJson(object));
    return object;
  }

  public float[] recordAndReturn(float[] object) {
    logInputHelper("float[]", gson.toJson(object));
    return object;
  }

  public char recordAndReturn(char object) {
    logInputHelper("char", gson.toJson(object));
    return object;
  }

  public char[] recordAndReturn(char[] object) {
    logInputHelper("char[]", gson.toJson(object));
    return object;
  }

  public double recordAndReturn(double object) {
    logInputHelper("double", gson.toJson(object));
    return object;
  }

  public double[] recordAndReturn(double[] object) {
    logInputHelper("double[]", gson.toJson(object));
    return object;
  }

  public String recordAndReturn(String object) {
    logInputHelper("String", gson.toJson(object));
    return object;
  }

  public int recordAndReturnCount(int object) {
    logInputHelper("int_count", gson.toJson(object));
    return object;
  }
  /* END INPUT METHODS */

  /* BEGIN RESULT METHODS */
  private void logOutputHelper(String type, String value, String location) {
    writeToFile(String.format("{\"log_type\": \"output\", \"type\": %s, \"value\": %s, \"location\": %s}", gson.toJson(type), value, location));
  }

  public <T> void logOutput(T obj, String location) {
    logOutputHelper("Object", gson.toJson(obj.toString()), location);
  }

  public void logOutput(boolean obj, String location) {
    logOutputHelper("boolean", gson.toJson(obj), location);
  }

  public void logOutput(boolean[] obj, String location) {
    logOutputHelper("boolean[]", gson.toJson(obj), location);
  }

  public void logOutput(byte obj, String location) {
    logOutputHelper("byte", gson.toJson(obj), location);
  }

  public void logOutput(byte[] obj, String location) {
    logOutputHelper("byte[]", gson.toJson(obj), location);
  }

  public void logOutput(char obj, String location) {
    logOutputHelper("char", gson.toJson(obj), location);
  }

  public void logOutput(char[] obj, String location) {
    logOutputHelper("char[]", gson.toJson(obj), location);
  }

  public void logOutput(int obj, String location) {
    logOutputHelper("int", gson.toJson(obj), location);
  }

  public void logOutput(int[] obj, String location) {
    logOutputHelper("int[]", gson.toJson(obj), location);
  }

  public void logOutput(short obj, String location) {
    logOutputHelper("short", gson.toJson(obj), location);
  }

  public void logOutput(short[] obj, String location) {
    logOutputHelper("short[]", gson.toJson(obj), location);
  }

  public void logOutput(float obj, String location) {
    logOutputHelper("float", gson.toJson(obj), location);
  }

  public void logOutput(float[] obj, String location) {
    logOutputHelper("float[]", gson.toJson(obj), location);
  }

  public void logOutput(double obj, String location) {
    logOutputHelper("double", gson.toJson(obj), location);
  }

  public void logOutput(double[] obj, String location) {
    logOutputHelper("double[]", gson.toJson(obj), location);
  }
  /* END RESULT METHODS */
}
