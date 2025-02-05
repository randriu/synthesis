#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[0] <= 1.5) {
		if (x[10] <= 1.0) {
			if (x[4] <= 3.5) {
				if (x[7] <= 1.5) {
					if (x[0] <= 0.5) {
						return 0.0f;
					}
					else {
						return 1.0f;
					}

				}
				else {
					if (x[7] <= 2.5) {
						if (x[4] <= 2.5) {
							if (x[2] <= 2.5) {
								if (x[3] <= 2.5) {
									if (x[4] <= 1.5) {
										return 4.0f;
									}
									else {
										return 7.0f;
									}

								}
								else {
									return 12.0f;
								}

							}
							else {
								return 14.0f;
							}

						}
						else {
							if (x[12] <= 3.0) {
								if (x[11] <= 3.0) {
									if (x[2] <= 5.5) {
										if (x[5] <= 3.5) {
											if (x[6] <= 3.5) {
												if (x[5] <= 2.5) {
													if (x[3] <= 0.5) {
														if (x[2] <= 0.5) {
															return 11.0f;
														}
														else {
															if (x[2] <= 1.5) {
																if (x[6] <= 2.5) {
																	return 13.0f;
																}
																else {
																	return 11.0f;
																}

															}
															else {
																return 11.0f;
															}

														}

													}
													else {
														if (x[3] <= 1.5) {
															return 9.0f;
														}
														else {
															return 11.0f;
														}

													}

												}
												else {
													return 11.0f;
												}

											}
											else {
												if (x[9] <= 1.5) {
													return 8.0f;
												}
												else {
													if (x[5] <= 2.5) {
														if (x[2] <= 2.5) {
															return 11.0f;
														}
														else {
															return 18.0f;
														}

													}
													else {
														return 11.0f;
													}

												}

											}

										}
										else {
											if (x[8] <= 1.5) {
												if (x[9] <= 2.5) {
													return 18.0f;
												}
												else {
													return 17.0f;
												}

											}
											else {
												if (x[3] <= 5.5) {
													if (x[0] <= 0.5) {
														if (x[8] <= 2.5) {
															if (x[3] <= 3.5) {
																if (x[6] <= 3.5) {
																	if (x[3] <= 2.5) {
																		return 11.0f;
																	}
																	else {
																		if (x[6] <= 2.5) {
																			return 16.0f;
																		}
																		else {
																			return 11.0f;
																		}

																	}

																}
																else {
																	if (x[3] <= 0.5) {
																		return 16.0f;
																	}
																	else {
																		if (x[3] <= 1.5) {
																			return 11.0f;
																		}
																		else {
																			if (x[3] <= 2.5) {
																				return 16.0f;
																			}
																			else {
																				return 11.0f;
																			}

																		}

																	}

																}

															}
															else {
																return 11.0f;
															}

														}
														else {
															if (x[2] <= 2.5) {
																if (x[2] <= 0.5) {
																	return 11.0f;
																}
																else {
																	if (x[2] <= 1.5) {
																		if (x[11] <= 1.0) {
																			return 18.0f;
																		}
																		else {
																			return 11.0f;
																		}

																	}
																	else {
																		if (x[11] <= 1.0) {
																			return 11.0f;
																		}
																		else {
																			return 18.0f;
																		}

																	}

																}

															}
															else {
																return 11.0f;
															}

														}

													}
													else {
														if (x[6] <= 3.5) {
															return 11.0f;
														}
														else {
															if (x[8] <= 2.5) {
																return 16.0f;
															}
															else {
																return 8.0f;
															}

														}

													}

												}
												else {
													if (x[6] <= 3.5) {
														return 16.0f;
													}
													else {
														if (x[3] <= 6.5) {
															return 11.0f;
														}
														else {
															if (x[3] <= 10.5) {
																if (x[3] <= 8.5) {
																	if (x[3] <= 7.5) {
																		return 16.0f;
																	}
																	else {
																		return 11.0f;
																	}

																}
																else {
																	return 16.0f;
																}

															}
															else {
																if (x[3] <= 12.5) {
																	return 11.0f;
																}
																else {
																	if (x[3] <= 13.5) {
																		return 16.0f;
																	}
																	else {
																		if (x[3] <= 14.5) {
																			return 11.0f;
																		}
																		else {
																			return 16.0f;
																		}

																	}

																}

															}

														}

													}

												}

											}

										}

									}
									else {
										if (x[6] <= 3.5) {
											return 11.0f;
										}
										else {
											if (x[5] <= 3.5) {
												return 18.0f;
											}
											else {
												if (x[2] <= 9.5) {
													if (x[2] <= 8.5) {
														if (x[11] <= 1.0) {
															if (x[2] <= 6.5) {
																return 18.0f;
															}
															else {
																if (x[2] <= 7.5) {
																	return 11.0f;
																}
																else {
																	return 18.0f;
																}

															}

														}
														else {
															if (x[2] <= 6.5) {
																return 11.0f;
															}
															else {
																if (x[2] <= 7.5) {
																	return 18.0f;
																}
																else {
																	return 11.0f;
																}

															}

														}

													}
													else {
														return 18.0f;
													}

												}
												else {
													if (x[2] <= 11.5) {
														if (x[2] <= 10.5) {
															if (x[11] <= 1.0) {
																return 11.0f;
															}
															else {
																return 18.0f;
															}

														}
														else {
															return 11.0f;
														}

													}
													else {
														if (x[2] <= 12.5) {
															if (x[11] <= 1.0) {
																return 18.0f;
															}
															else {
																return 11.0f;
															}

														}
														else {
															if (x[11] <= 1.0) {
																if (x[2] <= 13.5) {
																	return 11.0f;
																}
																else {
																	if (x[2] <= 14.5) {
																		return 18.0f;
																	}
																	else {
																		return 11.0f;
																	}

																}

															}
															else {
																if (x[2] <= 13.5) {
																	return 18.0f;
																}
																else {
																	if (x[2] <= 14.5) {
																		return 11.0f;
																	}
																	else {
																		return 18.0f;
																	}

																}

															}

														}

													}

												}

											}

										}

									}

								}
								else {
									if (x[9] <= 2.5) {
										return 18.0f;
									}
									else {
										if (x[6] <= 2.5) {
											return 11.0f;
										}
										else {
											if (x[5] <= 1.5) {
												if (x[11] <= 9.0) {
													if (x[11] <= 7.0) {
														if (x[11] <= 5.0) {
															return 11.0f;
														}
														else {
															return 17.0f;
														}

													}
													else {
														return 11.0f;
													}

												}
												else {
													return 17.0f;
												}

											}
											else {
												return 17.0f;
											}

										}

									}

								}

							}
							else {
								if (x[8] <= 2.5) {
									return 16.0f;
								}
								else {
									if (x[5] <= 2.5) {
										return 11.0f;
									}
									else {
										if (x[6] <= 1.5) {
											if (x[12] <= 9.0) {
												if (x[12] <= 7.0) {
													if (x[12] <= 5.0) {
														return 11.0f;
													}
													else {
														return 8.0f;
													}

												}
												else {
													return 11.0f;
												}

											}
											else {
												return 8.0f;
											}

										}
										else {
											return 8.0f;
										}

									}

								}

							}

						}

					}
					else {
						if (x[5] <= 2.5) {
							if (x[4] <= 1.5) {
								return 5.0f;
							}
							else {
								return 9.0f;
							}

						}
						else {
							if (x[5] <= 3.5) {
								if (x[6] <= 2.5) {
									if (x[1] <= 5.5) {
										if (x[1] <= 1.5) {
											if (x[1] <= 0.5) {
												return 13.0f;
											}
											else {
												return 12.0f;
											}

										}
										else {
											return 13.0f;
										}

									}
									else {
										return 12.0f;
									}

								}
								else {
									if (x[1] <= 4.5) {
										return 12.0f;
									}
									else {
										if (x[6] <= 3.5) {
											return 12.0f;
										}
										else {
											if (x[1] <= 6.5) {
												return 18.0f;
											}
											else {
												return 12.0f;
											}

										}

									}

								}

							}
							else {
								if (x[11] <= 1.0) {
									if (x[1] <= 0.5) {
										return 16.0f;
									}
									else {
										if (x[1] <= 1.5) {
											return 14.0f;
										}
										else {
											return 16.0f;
										}

									}

								}
								else {
									if (x[0] <= 0.5) {
										return 1.0f;
									}
									else {
										if (x[8] <= 2.0) {
											if (x[9] <= 2.5) {
												return 18.0f;
											}
											else {
												return 17.0f;
											}

										}
										else {
											return 8.0f;
										}

									}

								}

							}

						}

					}

				}

			}
			else {
				if (x[7] <= 2.5) {
					if (x[7] <= 1.5) {
						return 1.0f;
					}
					else {
						if (x[0] <= 0.5) {
							if (x[2] <= 0.5) {
								if (x[5] <= 3.5) {
									if (x[3] <= 5.5) {
										if (x[3] <= 1.5) {
											if (x[6] <= 3.5) {
												if (x[3] <= 0.5) {
													if (x[8] <= 2.5) {
														return 12.0f;
													}
													else {
														return 15.0f;
													}

												}
												else {
													return 15.0f;
												}

											}
											else {
												return 15.0f;
											}

										}
										else {
											if (x[6] <= 3.5) {
												if (x[3] <= 2.5) {
													return 12.0f;
												}
												else {
													return 15.0f;
												}

											}
											else {
												if (x[3] <= 2.5) {
													return 15.0f;
												}
												else {
													return 12.0f;
												}

											}

										}

									}
									else {
										if (x[3] <= 11.5) {
											return 15.0f;
										}
										else {
											if (x[3] <= 12.5) {
												return 12.0f;
											}
											else {
												return 15.0f;
											}

										}

									}

								}
								else {
									return 15.0f;
								}

							}
							else {
								if (x[6] <= 3.5) {
									if (x[2] <= 5.5) {
										if (x[5] <= 3.5) {
											if (x[2] <= 2.5) {
												if (x[2] <= 1.5) {
													if (x[11] <= 1.0) {
														return 14.0f;
													}
													else {
														return 15.0f;
													}

												}
												else {
													if (x[11] <= 1.0) {
														return 15.0f;
													}
													else {
														return 14.0f;
													}

												}

											}
											else {
												return 15.0f;
											}

										}
										else {
											if (x[2] <= 2.5) {
												return 15.0f;
											}
											else {
												return 14.0f;
											}

										}

									}
									else {
										if (x[2] <= 11.5) {
											return 15.0f;
										}
										else {
											if (x[2] <= 12.5) {
												return 14.0f;
											}
											else {
												return 15.0f;
											}

										}

									}

								}
								else {
									return 15.0f;
								}

							}

						}
						else {
							if (x[11] <= 1.0) {
								if (x[6] <= 2.5) {
									return 12.0f;
								}
								else {
									return 15.0f;
								}

							}
							else {
								if (x[12] <= 1.0) {
									if (x[5] <= 2.5) {
										return 14.0f;
									}
									else {
										return 15.0f;
									}

								}
								else {
									if (x[5] <= 2.5) {
										if (x[12] <= 7.0) {
											if (x[6] <= 2.5) {
												if (x[11] <= 7.0) {
													return 15.0f;
												}
												else {
													if (x[11] <= 9.0) {
														return 17.0f;
													}
													else {
														return 15.0f;
													}

												}

											}
											else {
												return 15.0f;
											}

										}
										else {
											if (x[12] <= 9.0) {
												return 8.0f;
											}
											else {
												return 15.0f;
											}

										}

									}
									else {
										return 15.0f;
									}

								}

							}

						}

					}

				}
				else {
					if (x[5] <= 3.5) {
						if (x[1] <= 5.5) {
							if (x[1] <= 1.5) {
								if (x[1] <= 0.5) {
									return 12.0f;
								}
								else {
									return 18.0f;
								}

							}
							else {
								return 12.0f;
							}

						}
						else {
							if (x[1] <= 9.5) {
								if (x[1] <= 7.5) {
									if (x[1] <= 6.5) {
										return 18.0f;
									}
									else {
										return 12.0f;
									}

								}
								else {
									return 18.0f;
								}

							}
							else {
								if (x[1] <= 11.5) {
									return 12.0f;
								}
								else {
									if (x[1] <= 12.5) {
										return 18.0f;
									}
									else {
										if (x[1] <= 13.5) {
											return 12.0f;
										}
										else {
											if (x[1] <= 14.5) {
												return 18.0f;
											}
											else {
												return 12.0f;
											}

										}

									}

								}

							}

						}

					}
					else {
						if (x[11] <= 1.0) {
							if (x[6] <= 3.5) {
								if (x[1] <= 4.5) {
									if (x[1] <= 1.5) {
										return 16.0f;
									}
									else {
										return 14.0f;
									}

								}
								else {
									if (x[1] <= 14.5) {
										if (x[1] <= 10.5) {
											return 16.0f;
										}
										else {
											if (x[1] <= 11.5) {
												return 14.0f;
											}
											else {
												return 16.0f;
											}

										}

									}
									else {
										return 14.0f;
									}

								}

							}
							else {
								return 16.0f;
							}

						}
						else {
							if (x[0] <= 0.5) {
								return 1.0f;
							}
							else {
								if (x[8] <= 2.0) {
									if (x[9] <= 2.5) {
										return 18.0f;
									}
									else {
										return 17.0f;
									}

								}
								else {
									return 8.0f;
								}

							}

						}

					}

				}

			}

		}
		else {
			if (x[0] <= 0.5) {
				if (x[1] <= 0.5) {
					return 0.0f;
				}
				else {
					if (x[8] <= 2.5) {
						if (x[5] <= 3.5) {
							if (x[5] <= 2.5) {
								if (x[1] <= 2.5) {
									return 9.0f;
								}
								else {
									return 14.0f;
								}

							}
							else {
								if (x[1] <= 5.5) {
									if (x[6] <= 2.5) {
										if (x[1] <= 1.5) {
											return 13.0f;
										}
										else {
											return 12.0f;
										}

									}
									else {
										if (x[6] <= 3.5) {
											return 12.0f;
										}
										else {
											if (x[1] <= 3.5) {
												if (x[1] <= 1.5) {
													return 12.0f;
												}
												else {
													if (x[4] <= 2.5) {
														if (x[1] <= 2.5) {
															return 12.0f;
														}
														else {
															return 18.0f;
														}

													}
													else {
														if (x[1] <= 2.5) {
															if (x[4] <= 3.5) {
																return 12.0f;
															}
															else {
																return 18.0f;
															}

														}
														else {
															return 12.0f;
														}

													}

												}

											}
											else {
												return 12.0f;
											}

										}

									}

								}
								else {
									if (x[6] <= 3.5) {
										return 12.0f;
									}
									else {
										if (x[4] <= 3.5) {
											return 18.0f;
										}
										else {
											if (x[1] <= 6.5) {
												return 12.0f;
											}
											else {
												if (x[1] <= 10.5) {
													if (x[1] <= 8.5) {
														if (x[1] <= 7.5) {
															return 18.0f;
														}
														else {
															return 12.0f;
														}

													}
													else {
														return 18.0f;
													}

												}
												else {
													if (x[1] <= 12.5) {
														return 12.0f;
													}
													else {
														if (x[1] <= 13.5) {
															return 18.0f;
														}
														else {
															if (x[1] <= 14.5) {
																return 12.0f;
															}
															else {
																return 18.0f;
															}

														}

													}

												}

											}

										}

									}

								}

							}

						}
						else {
							if (x[6] <= 3.5) {
								if (x[1] <= 5.5) {
									if (x[1] <= 1.5) {
										return 16.0f;
									}
									else {
										if (x[4] <= 3.5) {
											if (x[1] <= 2.5) {
												return 14.0f;
											}
											else {
												return 16.0f;
											}

										}
										else {
											if (x[1] <= 2.5) {
												return 16.0f;
											}
											else {
												return 14.0f;
											}

										}

									}

								}
								else {
									if (x[1] <= 11.5) {
										return 16.0f;
									}
									else {
										if (x[1] <= 12.5) {
											return 14.0f;
										}
										else {
											return 16.0f;
										}

									}

								}

							}
							else {
								return 16.0f;
							}

						}

					}
					else {
						return 1.0f;
					}

				}

			}
			else {
				if (x[7] <= 2.0) {
					if (x[8] <= 2.5) {
						if (x[5] <= 3.5) {
							if (x[9] <= 2.5) {
								return 18.0f;
							}
							else {
								if (x[6] <= 2.5) {
									if (x[5] <= 2.5) {
										return 9.0f;
									}
									else {
										return 12.0f;
									}

								}
								else {
									if (x[10] <= 3.0) {
										if (x[4] <= 3.5) {
											return 12.0f;
										}
										else {
											return 17.0f;
										}

									}
									else {
										if (x[4] <= 1.5) {
											if (x[10] <= 9.0) {
												if (x[10] <= 7.0) {
													if (x[10] <= 5.0) {
														return 12.0f;
													}
													else {
														return 17.0f;
													}

												}
												else {
													return 12.0f;
												}

											}
											else {
												return 17.0f;
											}

										}
										else {
											return 17.0f;
										}

									}

								}

							}

						}
						else {
							if (x[9] <= 2.5) {
								return 14.0f;
							}
							else {
								if (x[6] <= 2.5) {
									if (x[4] <= 1.5) {
										if (x[10] <= 7.0) {
											return 16.0f;
										}
										else {
											if (x[10] <= 9.0) {
												return 17.0f;
											}
											else {
												return 16.0f;
											}

										}

									}
									else {
										return 16.0f;
									}

								}
								else {
									return 16.0f;
								}

							}

						}

					}
					else {
						if (x[2] <= 0.5) {
							if (x[8] <= 3.5) {
								if (x[10] <= 29.0) {
									return 8.0f;
								}
								else {
									if (x[3] <= 0.5) {
										if (x[9] <= 3.5) {
											return 19.0f;
										}
										else {
											return 8.0f;
										}

									}
									else {
										return 8.0f;
									}

								}

							}
							else {
								if (x[9] <= 2.5) {
									return 18.0f;
								}
								else {
									return 17.0f;
								}

							}

						}
						else {
							if (x[9] <= 2.5) {
								return 18.0f;
							}
							else {
								return 17.0f;
							}

						}

					}

				}
				else {
					if (x[1] <= 0.5) {
						if (x[11] <= 29.0) {
							if (x[12] <= 29.0) {
								return 10.0f;
							}
							else {
								if (x[2] <= 0.5) {
									if (x[8] <= 3.5) {
										return 21.0f;
									}
									else {
										return 10.0f;
									}

								}
								else {
									return 10.0f;
								}

							}

						}
						else {
							if (x[3] <= 0.5) {
								if (x[9] <= 3.5) {
									return 20.0f;
								}
								else {
									return 10.0f;
								}

							}
							else {
								return 10.0f;
							}

						}

					}
					else {
						if (x[8] <= 1.5) {
							if (x[9] <= 2.5) {
								return 18.0f;
							}
							else {
								return 17.0f;
							}

						}
						else {
							if (x[8] <= 2.5) {
								return 16.0f;
							}
							else {
								return 8.0f;
							}

						}

					}

				}

			}

		}

	}
	else {
		if (x[7] <= 3.5) {
			if (x[8] <= 3.5) {
				if (x[9] <= 3.5) {
					if (x[1] <= 0.5) {
						if (x[2] <= 0.5) {
							if (x[3] <= 0.5) {
								if (x[9] <= 2.0) {
									if (x[9] <= 0.5) {
										return 2.0f;
									}
									else {
										return 3.0f;
									}

								}
								else {
									return 2.0f;
								}

							}
							else {
								return 6.0f;
							}

						}
						else {
							return 6.0f;
						}

					}
					else {
						return 6.0f;
					}

				}
				else {
					return 3.0f;
				}

			}
			else {
				return 3.0f;
			}

		}
		else {
			return 3.0f;
		}

	}

}