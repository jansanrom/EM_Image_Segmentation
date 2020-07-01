import tensorflow as tf
from tensorflow.keras import Model, Input
from tensorflow.keras.layers import Dropout, Lambda, SpatialDropout3D, Conv3D, \
                                    Conv3DTranspose, MaxPooling3D, concatenate
from metrics import binary_crossentropy_weighted, jaccard_index, \
                    weighted_bce_dice_loss

def U_Net_3D(image_shape, activation='elu', numInitChannels=16, fixed_dropout=0.0, 
          spatial_dropout=False, loss_type="bce", optimizer="sgd", lr=0.001,
          fine_tunning=False):
    """Create the U-Net

       Args:
            image_shape (3D tuple): dimensions of the input image.

            activation (str, optional): Keras available activation type.

            numInitChannels (int, optional): number of convolution channels to
            start with. In each downsampling/upsampling the number of filters
            are multiplied/divided by 2.

            fixed_dropout (float, optional): dropout value to be fixed. If no
            value is provided the default behaviour will be to select a
            piramidal value stating from 0.1 and reaching 0.3 value.

            spatial_dropout (bool, optional): use spatial dropout instead of the
            "normal" dropout.

            loss_type (str, optional): loss type to use, three type available: 
            "bce" (Binary Cross Entropy) , "w_bce" (Weighted BCE, based on
            weigth maps) and "w_bce_dice" (Weighted loss: weight1*BCE + weight2*Dice). 

            optimizer (str, optional): optimizer used to minimize the loss
            function. Posible options: 'sgd' or 'adam'.

            lr (float, optional): learning rate value.
        
            fine_tunning (bool, optional): flag to freeze the encoder part for 
            fine tuning.

       Returns:
            model (Keras model): model containing the U-Net created.
    """
    #dinamic_dim = (None,)*(len(image_shape)-1) + (1,)
    #inputs = Input(dinamic_dim)
    inputs = Input(image_shape)
        
    if loss_type == "w_bce":
        weights = Input(image_shape)

    c1 = Conv3D(numInitChannels, (3, 3, 3), activation=activation,
                kernel_initializer='he_normal', padding='same') (inputs)
    if fixed_dropout == 0.0:
        c1 = SpatialDropout3D(0.1) (c1) if spatial_dropout == True else Dropout(0.1) (c1)
    else:
        c1 = SpatialDropout3D(fixed_dropout) (c1) if spatial_dropout == True else Dropout(fixed_dropout) (c1)

    c1 = Conv3D(numInitChannels, (3, 3, 3), activation=activation,
                kernel_initializer='he_normal', padding='same') (c1)
    p1 = MaxPooling3D((2, 2, 2)) (c1)
    
    c2 = Conv3D(numInitChannels*2, (3, 3, 3), activation=activation,
                kernel_initializer='he_normal', padding='same') (p1)
    if fixed_dropout == 0.0:
        c2 = SpatialDropout3D(0.1) (c2) if spatial_dropout == True else Dropout(0.1) (c2)
    else:
        c2 = SpatialDropout3D(fixed_dropout) (c2) if spatial_dropout == True else Dropout(fixed_dropout) (c2)
    c2 = Conv3D(numInitChannels*2, (3, 3, 3), activation=activation,
                kernel_initializer='he_normal', padding='same') (c2)
    p2 = MaxPooling3D((2, 2, 2)) (c2)
    
    c3 = Conv3D(numInitChannels*4, (3, 3, 3), activation=activation,
                kernel_initializer='he_normal', padding='same') (p2)
    if fixed_dropout == 0.0:
        c3 = SpatialDropout3D(0.2) (c3) if spatial_dropout == True else Dropout(0.2) (c3)
    else:    
        c3 = SpatialDropout3D(fixed_dropout) (c3) if spatial_dropout == True else Dropout(fixed_dropout) (c3)
    c3 = Conv3D(numInitChannels*4, (3, 3, 3), activation=activation,
                kernel_initializer='he_normal', padding='same') (c3)
    p3 = MaxPooling3D((2, 2, 2)) (c3)
    
    c4 = Conv3D(numInitChannels*8, (3, 3, 3), activation=activation,
                kernel_initializer='he_normal', padding='same') (p3)
    if fixed_dropout == 0.0:
        c4 = SpatialDropout3D(0.2) (c4) if spatial_dropout == True else Dropout(0.2) (c4)
    else:
        c4 = SpatialDropout3D(fixed_dropout) (c4) if spatial_dropout == True else Dropout(fixed_dropout) (c4)
    c4 = Conv3D(numInitChannels*8, (3, 3, 3), activation=activation,
                kernel_initializer='he_normal', padding='same') (c4)
    p4 = MaxPooling3D(pool_size=(2, 2, 2)) (c4)
    
    c5 = Conv3D(numInitChannels*16, (3, 3, 3), activation=activation,
                kernel_initializer='he_normal', padding='same') (p4)
    if fixed_dropout == 0.0:
        c5 = SpatialDropout3D(0.3) (c5) if spatial_dropout == True else Dropout(0.3) (c5)
    else:
        c5 = SpatialDropout3D(fixed_dropout) (c5) if spatial_dropout == True else Dropout(fixed_dropout) (c5)
    c5 = Conv3D(numInitChannels*16, (3, 3, 3), activation=activation,
                kernel_initializer='he_normal', padding='same') (c5)
    
    u6 = Conv3DTranspose(numInitChannels*8, (2, 2, 2), strides=(2, 2, 2),
                         padding='same') (c5)
    u6 = concatenate([u6, c4])
    c6 = Conv3D(numInitChannels*8, (3, 3, 3), activation=activation,
                kernel_initializer='he_normal', padding='same') (u6)
    if fixed_dropout == 0.0:
        c6 = SpatialDropout3D(0.2) (c6) if spatial_dropout == True else Dropout(0.2) (c6)
    else:
        c6 = SpatialDropout3D(fixed_dropout) (c6) if spatial_dropout == True else Dropout(fixed_dropout) (c6)
    c6 = Conv3D(numInitChannels*8, (3, 3, 3), activation=activation,
                kernel_initializer='he_normal', padding='same') (c6)
    
    u7 = Conv3DTranspose(numInitChannels*4, (2, 2, 2), strides=(2, 2, 2),
                         padding='same') (c6)
    u7 = concatenate([u7, c3])
    c7 = Conv3D(numInitChannels*4, (3, 3, 3), activation=activation,
                kernel_initializer='he_normal', padding='same') (u7)
    if fixed_dropout == 0.0:
        c7 = SpatialDropout3D(0.2) (c7) if spatial_dropout == True else Dropout(0.2) (c7)
    else:
        c7 = SpatialDropout3D(fixed_dropout) (c7) if spatial_dropout == True else Dropout(fixed_dropout) (c7)
    c7 = Conv3D(numInitChannels*4, (3, 3, 3), activation=activation,
                kernel_initializer='he_normal', padding='same') (c7)
    
    u8 = Conv3DTranspose(numInitChannels*2, (2, 2, 2), strides=(2, 2, 2),
                         padding='same') (c7)
    u8 = concatenate([u8, c2])
    c8 = Conv3D(numInitChannels*2, (3, 3, 3), activation=activation,
                kernel_initializer='he_normal', padding='same') (u8)
    if fixed_dropout == 0.0:
        c8 = SpatialDropout3D(0.1) (c8) if spatial_dropout == True else Dropout(0.1) (c8)
    else:
        c8 = SpatialDropout3D(fixed_dropout) (c8) if spatial_dropout == True else Dropout(fixed_dropout) (c8)
    c8 = Conv3D(numInitChannels*2, (3, 3, 3), activation=activation,
                kernel_initializer='he_normal', padding='same') (c8)
    
    u9 = Conv3DTranspose(numInitChannels, (2, 2, 2), strides=(2, 2, 2),
                         padding='same') (c8)
    u9 = concatenate([u9, c1])
    c9 = Conv3D(numInitChannels, (3, 3, 3), activation=activation,
                kernel_initializer='he_normal', padding='same') (u9)
    if fixed_dropout == 0.0:
        c9 = SpatialDropout3D(0.1) (c9) if spatial_dropout == True else Dropout(0.1) (c9)
    else:
        c9 = SpatialDropout3D(fixed_dropout) (c9) if spatial_dropout == True else Dropout(fixed_dropout) (c9)
    c9 = Conv3D(numInitChannels, (3, 3, 3), activation=activation,
                kernel_initializer='he_normal', padding='same') (c9)
    
    outputs = Conv3D(1, (1, 1, 1), activation='sigmoid') (c9)
  
    # Loss type 
    if loss_type == "w_bce":
        model = Model(inputs=[inputs, weights], outputs=[outputs]) 
    else:
        model = Model(inputs=[inputs], outputs=[outputs])
    
    # Select the optimizer
    if optimizer == "sgd":
        opt = tf.keras.optimizers.SGD(
            lr=lr, momentum=0.99, decay=0.0, nesterov=False)
    elif optimizer == "adam":
        opt = tf.keras.optimizers.Adam(
            lr=lr, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0, 
            amsgrad=False)
    else:
        raise ValueError("Error: optimizer value must be 'sgd' or 'adam'")
        
    # Fine tunning: freeze the enconder part
    if fine_tunning == True:
        print("Freezing the contracting path of the U-Net for fine tunning . . .")
        for layer in model.layers[:20]:
            layer.trainable = False
        for layer in model.layers:
            print("{}: {}".format(layer, layer.trainable))

    # Compile the model
    if loss_type == "bce":
        model.compile(optimizer=opt, loss='binary_crossentropy', 
                      metrics=[jaccard_index])
    elif loss_type == "w_bce":
        model.compile(optimizer=opt, loss=binary_crossentropy_weighted(weights), 
                      metrics=[jaccard_index])
    elif loss_type == "w_bce_dice":
        model.compile(optimizer=opt, 
                      loss=weighted_bce_dice_loss(w_dice=0.66, w_bce=0.33),
                      metrics=[jaccard_index])
    else:
        raise ValueError("'loss_type' must be 'bce', 'w_bce' or 'w_bce_dice'")

    return model
