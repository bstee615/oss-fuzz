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
public final class MyRecordedFuzzedDataProvider implements FuzzedDataProvider, AutoCloseable {
  private FuzzedDataProvider provider;
  private Gson gson;
  private Writer writer;

  public MyRecordedFuzzedDataProvider(FuzzedDataProvider provider, String baseDir, String fuzzerTargetName) {
    System.err.println(String.format("GREAT! Instrumented the class. provider.remainingBytes(): %d baseDir: \"%s\" fuzzerTargetName: \"%s\"", provider.remainingBytes(), baseDir, fuzzerTargetName));
    this.provider = provider;
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

  private void writeToFile(String string) {
    System.err.println(String.format("WRITE TO FILE: \"%s\"", string));
    try {
        this.writer.append(string + "\n");
    }
    catch (IOException ex) {
        System.err.printf("Error writing to file: %s%n", string);
    }
  }

  private String encodeData(String type, String value) {
    StackTraceElement[] stackTrace = Thread.currentThread().getStackTrace();
    return String.format("{\"type\": \"%s\", \"value\": %s, \"stacktrace\": %s}", type, value, gson.toJson(stackTrace));
  }

  private String encodeData(String type) {
    return encodeData(type, null);
  }

  /* END GENERATED METHODS */
  private boolean recordAndReturn(boolean object) {
    writeToFile(encodeData("boolean", gson.toJson(object)));
    return object;
  }

  private boolean[] recordAndReturn(boolean[] object) {
    writeToFile(encodeData("boolean[]", gson.toJson(object)));
    return object;
  }

  private byte recordAndReturn(byte object) {
    writeToFile(encodeData("byte", gson.toJson(object)));
    return object;
  }

  private byte[] recordAndReturn(byte[] object) {
    writeToFile(encodeData("byte[]", gson.toJson(object)));
    return object;
  }

  private short recordAndReturn(short object) {
    writeToFile(encodeData("short", gson.toJson(object)));
    return object;
  }

  private short[] recordAndReturn(short[] object) {
    writeToFile(encodeData("short[]", gson.toJson(object)));
    return object;
  }

  private long recordAndReturn(long object) {
    writeToFile(encodeData("long", gson.toJson(object)));
    return object;
  }

  private long[] recordAndReturn(long[] object) {
    writeToFile(encodeData("long[]", gson.toJson(object)));
    return object;
  }

  private int recordAndReturn(int object) {
    writeToFile(encodeData("int", gson.toJson(object)));
    return object;
  }

  private int[] recordAndReturn(int[] object) {
    writeToFile(encodeData("int[]", gson.toJson(object)));
    return object;
  }

  private float recordAndReturn(float object) {
    writeToFile(encodeData("float", gson.toJson(object)));
    return object;
  }

  private float[] recordAndReturn(float[] object) {
    writeToFile(encodeData("float[]", gson.toJson(object)));
    return object;
  }

  private char recordAndReturn(char object) {
    writeToFile(encodeData("char", gson.toJson(object)));
    return object;
  }

  private char[] recordAndReturn(char[] object) {
    writeToFile(encodeData("char[]", gson.toJson(object)));
    return object;
  }

  private double recordAndReturn(double object) {
    writeToFile(encodeData("double", gson.toJson(object)));
    return object;
  }

  private double[] recordAndReturn(double[] object) {
    writeToFile(encodeData("double[]", gson.toJson(object)));
    return object;
  }

  private String recordAndReturn(String object) {
    writeToFile(encodeData("String", gson.toJson(object)));
    return object;
  }

  private int recordAndReturnCount(int object) {
    writeToFile(encodeData("int_count", gson.toJson(object)));
    return object;
  }
  /* END GENERATED METHODS */
  
  public void markBeginFuzzer() {
    writeToFile(encodeData("begin"));
  }
  
  public void markEndFuzzer() {
    writeToFile(encodeData("end"));
  }

  @Override
  public boolean consumeBoolean() {
    return recordAndReturn(provider.consumeBoolean());
  }

  @Override
  public boolean[] consumeBooleans(int maxLength) {
    return recordAndReturn(provider.consumeBooleans(maxLength));
  }

  @Override
  public byte consumeByte() {
    return recordAndReturn(provider.consumeByte());
  }

  @Override
  public byte consumeByte(byte min, byte max) {
    return recordAndReturn(provider.consumeByte(min, max));
  }

  @Override
  public byte[] consumeBytes(int maxLength) {
    return recordAndReturn(provider.consumeBytes(maxLength));
  }

  @Override
  public byte[] consumeRemainingAsBytes() {
    return recordAndReturn(provider.consumeRemainingAsBytes());
  }

  @Override
  public short consumeShort() {
    return recordAndReturn(provider.consumeShort());
  }

  @Override
  public short consumeShort(short min, short max) {
    return recordAndReturn(provider.consumeShort(min, max));
  }

  @Override
  public short[] consumeShorts(int maxLength) {
    return recordAndReturn(provider.consumeShorts(maxLength));
  }

  @Override
  public int consumeInt() {
    return recordAndReturn(provider.consumeInt());
  }

  @Override
  public int consumeInt(int min, int max) {
    return recordAndReturn(provider.consumeInt(min, max));
  }

  @Override
  public int[] consumeInts(int maxLength) {
    return recordAndReturn(provider.consumeInts(maxLength));
  }

  @Override
  public long consumeLong() {
    return recordAndReturn(provider.consumeLong());
  }

  @Override
  public long consumeLong(long min, long max) {
    return recordAndReturn(provider.consumeLong(min, max));
  }

  @Override
  public long[] consumeLongs(int maxLength) {
    return recordAndReturn(provider.consumeLongs(maxLength));
  }

  @Override
  public float consumeFloat() {
    return recordAndReturn(provider.consumeFloat());
  }

  @Override
  public float consumeRegularFloat() {
    return recordAndReturn(provider.consumeRegularFloat());
  }

  @Override
  public float consumeRegularFloat(float min, float max) {
    return recordAndReturn(provider.consumeRegularFloat(min, max));
  }

  @Override
  public float consumeProbabilityFloat() {
    return recordAndReturn(provider.consumeProbabilityFloat());
  }

  @Override
  public double consumeDouble() {
    return recordAndReturn(provider.consumeDouble());
  }

  @Override
  public double consumeRegularDouble() {
    return recordAndReturn(provider.consumeRegularDouble());
  }

  @Override
  public double consumeRegularDouble(double min, double max) {
    return recordAndReturn(provider.consumeRegularDouble(min, max));
  }

  @Override
  public double consumeProbabilityDouble() {
    return recordAndReturn(provider.consumeProbabilityDouble());
  }

  @Override
  public char consumeChar() {
    return recordAndReturn(provider.consumeChar());
  }

  @Override
  public char consumeChar(char min, char max) {
    return recordAndReturn(provider.consumeChar(min, max));
  }

  @Override
  public char consumeCharNoSurrogates() {
    return recordAndReturn(provider.consumeCharNoSurrogates());
  }

  @Override
  public String consumeString(int maxLength) {
    return recordAndReturn(provider.consumeString(maxLength));
  }

  @Override
  public String consumeRemainingAsString() {
    return recordAndReturn(provider.consumeRemainingAsString());
  }

  @Override
  public String consumeAsciiString(int maxLength) {
    return recordAndReturn(provider.consumeAsciiString(maxLength));
  }

  @Override
  public String consumeRemainingAsAsciiString() {
    return recordAndReturn(provider.consumeRemainingAsAsciiString());
  }

  @Override
  public int remainingBytes() {
    return recordAndReturnCount(provider.remainingBytes());
  }
}
