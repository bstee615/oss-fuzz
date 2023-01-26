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
import java.lang.Thread;
import java.lang.StackTraceElement;
import com.google.gson.Gson;

// Wraps the native FuzzedDataProvider and serializes all its return values as JSONL.
public final class FuzzedDataProviderRecorderWrapper implements FuzzedDataProvider {
  private FuzzedDataProvider provider;
  private FuzzerRecorder inputRecorder;

  public FuzzedDataProviderRecorderWrapper(FuzzedDataProvider provider, FuzzerRecorder inputRecorder) {
    this.provider = provider;
    this.inputRecorder = inputRecorder;
  }

  public FuzzedDataProviderRecorderWrapper setLocation(String location) {
    inputRecorder.setLocation(location);
    return this;
  }

  @Override
  public boolean consumeBoolean() {
    return inputRecorder.recordAndReturn(provider.consumeBoolean());
  }

  @Override
  public boolean[] consumeBooleans(int maxLength) {
    return inputRecorder.recordAndReturn(provider.consumeBooleans(maxLength));
  }

  @Override
  public byte consumeByte() {
    return inputRecorder.recordAndReturn(provider.consumeByte());
  }

  @Override
  public byte consumeByte(byte min, byte max) {
    return inputRecorder.recordAndReturn(provider.consumeByte(min, max));
  }

  @Override
  public byte[] consumeBytes(int maxLength) {
    return inputRecorder.recordAndReturn(provider.consumeBytes(maxLength));
  }

  @Override
  public byte[] consumeRemainingAsBytes() {
    return inputRecorder.recordAndReturn(provider.consumeRemainingAsBytes());
  }

  @Override
  public short consumeShort() {
    return inputRecorder.recordAndReturn(provider.consumeShort());
  }

  @Override
  public short consumeShort(short min, short max) {
    return inputRecorder.recordAndReturn(provider.consumeShort(min, max));
  }

  @Override
  public short[] consumeShorts(int maxLength) {
    return inputRecorder.recordAndReturn(provider.consumeShorts(maxLength));
  }

  @Override
  public int consumeInt() {
    return inputRecorder.recordAndReturn(provider.consumeInt());
  }

  @Override
  public int consumeInt(int min, int max) {
    return inputRecorder.recordAndReturn(provider.consumeInt(min, max));
  }

  @Override
  public int[] consumeInts(int maxLength) {
    return inputRecorder.recordAndReturn(provider.consumeInts(maxLength));
  }

  @Override
  public long consumeLong() {
    return inputRecorder.recordAndReturn(provider.consumeLong());
  }

  @Override
  public long consumeLong(long min, long max) {
    return inputRecorder.recordAndReturn(provider.consumeLong(min, max));
  }

  @Override
  public long[] consumeLongs(int maxLength) {
    return inputRecorder.recordAndReturn(provider.consumeLongs(maxLength));
  }

  @Override
  public float consumeFloat() {
    return inputRecorder.recordAndReturn(provider.consumeFloat());
  }

  @Override
  public float consumeRegularFloat() {
    return inputRecorder.recordAndReturn(provider.consumeRegularFloat());
  }

  @Override
  public float consumeRegularFloat(float min, float max) {
    return inputRecorder.recordAndReturn(provider.consumeRegularFloat(min, max));
  }

  @Override
  public float consumeProbabilityFloat() {
    return inputRecorder.recordAndReturn(provider.consumeProbabilityFloat());
  }

  @Override
  public double consumeDouble() {
    return inputRecorder.recordAndReturn(provider.consumeDouble());
  }

  @Override
  public double consumeRegularDouble() {
    return inputRecorder.recordAndReturn(provider.consumeRegularDouble());
  }

  @Override
  public double consumeRegularDouble(double min, double max) {
    return inputRecorder.recordAndReturn(provider.consumeRegularDouble(min, max));
  }

  @Override
  public double consumeProbabilityDouble() {
    return inputRecorder.recordAndReturn(provider.consumeProbabilityDouble());
  }

  @Override
  public char consumeChar() {
    return inputRecorder.recordAndReturn(provider.consumeChar());
  }

  @Override
  public char consumeChar(char min, char max) {
    return inputRecorder.recordAndReturn(provider.consumeChar(min, max));
  }

  @Override
  public char consumeCharNoSurrogates() {
    return inputRecorder.recordAndReturn(provider.consumeCharNoSurrogates());
  }

  @Override
  public String consumeString(int maxLength) {
    return inputRecorder.recordAndReturn(provider.consumeString(maxLength));
  }

  @Override
  public String consumeRemainingAsString() {
    return inputRecorder.recordAndReturn(provider.consumeRemainingAsString());
  }

  @Override
  public String consumeAsciiString(int maxLength) {
    return inputRecorder.recordAndReturn(provider.consumeAsciiString(maxLength));
  }

  @Override
  public String consumeRemainingAsAsciiString() {
    return inputRecorder.recordAndReturn(provider.consumeRemainingAsAsciiString());
  }

  @Override
  public int remainingBytes() {
    return inputRecorder.recordAndReturnCount(provider.remainingBytes());
  }
}
